"""Logging handler that applies governance and passes events to a queue."""
from __future__ import annotations

import atexit
import logging
import queue
import threading
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional, Protocol

from .evaluator import evaluate_event
from .loader import RulesetLoader


class QueueSink(Protocol):
    """Protocol for queue sinks that receive governed events."""

    def send(self, event: Dict[str, Any], tags: Dict[str, Any]) -> None:
        """Send a governed event and its tags to the sink."""
        ...


@dataclass
class QueueHandlerMetrics:
    """Thread-safe metrics for monitoring CerbiQueueHandler health.

    Use these metrics to:
    - Monitor throughput (emitted_count, processed_count)
    - Detect backpressure issues (dropped_count)
    - Track sink reliability (sink_error_count)
    - Alert on governance issues (governance_error_count)
    """

    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)
    _emitted: int = field(default=0, repr=False)
    _processed: int = field(default=0, repr=False)
    _dropped: int = field(default=0, repr=False)
    _sink_errors: int = field(default=0, repr=False)
    _governance_errors: int = field(default=0, repr=False)

    @property
    def emitted_count(self) -> int:
        """Total events emitted to the handler."""
        with self._lock:
            return self._emitted

    @property
    def processed_count(self) -> int:
        """Events successfully sent to sink."""
        with self._lock:
            return self._processed

    @property
    def dropped_count(self) -> int:
        """Events dropped due to queue full (backpressure)."""
        with self._lock:
            return self._dropped

    @property
    def sink_error_count(self) -> int:
        """Sink send failures (errors swallowed)."""
        with self._lock:
            return self._sink_errors

    @property
    def governance_error_count(self) -> int:
        """Governance evaluation errors."""
        with self._lock:
            return self._governance_errors

    def _inc_emitted(self) -> None:
        with self._lock:
            self._emitted += 1

    def _inc_processed(self) -> None:
        with self._lock:
            self._processed += 1

    def _inc_dropped(self) -> None:
        with self._lock:
            self._dropped += 1

    def _inc_sink_error(self) -> None:
        with self._lock:
            self._sink_errors += 1

    def _inc_governance_error(self) -> None:
        with self._lock:
            self._governance_errors += 1

    def snapshot(self) -> Dict[str, int]:
        """Return a point-in-time snapshot of all metrics."""
        with self._lock:
            return {
                "emitted_count": self._emitted,
                "processed_count": self._processed,
                "dropped_count": self._dropped,
                "sink_error_count": self._sink_errors,
                "governance_error_count": self._governance_errors,
            }


class InMemoryQueueSink:
    """A simple in-memory sink for testing and debugging."""

    def __init__(self) -> None:
        self._events: list[tuple[Dict[str, Any], Dict[str, Any]]] = []
        self._lock = threading.Lock()

    def send(self, event: Dict[str, Any], tags: Dict[str, Any]) -> None:
        with self._lock:
            self._events.append((event, tags))

    @property
    def events(self) -> list[tuple[Dict[str, Any], Dict[str, Any]]]:
        with self._lock:
            return list(self._events)

    def clear(self) -> None:
        with self._lock:
            self._events.clear()


class CallbackQueueSink:
    """A sink that invokes a callback for each event."""

    def __init__(self, callback: Callable[[Dict[str, Any], Dict[str, Any]], None]) -> None:
        self._callback = callback

    def send(self, event: Dict[str, Any], tags: Dict[str, Any]) -> None:
        self._callback(event, tags)


class FallbackSink:
    """A sink that tries a primary sink first, then falls back to a secondary.
    
    Use this for resilience when your primary destination (e.g., Kafka) might be
    unavailable. The fallback could write to a local file, stderr, or another queue.
    
    Example:
        >>> primary = CallbackQueueSink(lambda e, t: kafka.send(e))
        >>> fallback = CallbackQueueSink(lambda e, t: write_to_file(e))
        >>> sink = FallbackSink(primary, fallback)
    """

    def __init__(
        self,
        primary: QueueSink,
        fallback: QueueSink,
        *,
        on_fallback: Optional[Callable[[Exception, Dict[str, Any], Dict[str, Any]], None]] = None,
    ) -> None:
        """Initialize the fallback sink.
        
        Args:
            primary: The primary sink to try first.
            fallback: The fallback sink to use if primary fails.
            on_fallback: Optional callback when fallback is used. Signature: (exception, event, tags).
        """
        self._primary = primary
        self._fallback = fallback
        self._on_fallback = on_fallback
        self._fallback_count = 0
        self._lock = threading.Lock()

    def send(self, event: Dict[str, Any], tags: Dict[str, Any]) -> None:
        try:
            self._primary.send(event, tags)
        except Exception as exc:
            with self._lock:
                self._fallback_count += 1
            if self._on_fallback:
                try:
                    self._on_fallback(exc, event, tags)
                except Exception:
                    pass
            # Try fallback - if this also fails, let it propagate
            self._fallback.send(event, tags)

    @property
    def fallback_count(self) -> int:
        """Number of times fallback was used."""
        with self._lock:
            return self._fallback_count


class CircuitBreakerSink:
    """A sink wrapper that implements circuit breaker pattern.
    
    Prevents hammering a failing sink by "opening" the circuit after consecutive
    failures, then periodically testing if the sink has recovered.
    
    States:
    - CLOSED: Normal operation, all events go to sink
    - OPEN: Sink is failing, events go to fallback (if provided) or are dropped
    - HALF_OPEN: Testing if sink recovered, single event sent as probe
    
    Example:
        >>> sink = CircuitBreakerSink(
        ...     sink=CallbackQueueSink(kafka_send),
        ...     fallback=CallbackQueueSink(file_write),
        ...     failure_threshold=5,
        ...     recovery_timeout=30.0,
        ... )
    """

    def __init__(
        self,
        sink: QueueSink,
        fallback: Optional[QueueSink] = None,
        *,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        on_state_change: Optional[Callable[[str, str], None]] = None,
    ) -> None:
        """Initialize the circuit breaker.
        
        Args:
            sink: The underlying sink to protect.
            fallback: Optional fallback sink when circuit is open.
            failure_threshold: Consecutive failures before opening circuit.
            recovery_timeout: Seconds before attempting recovery (half-open).
            on_state_change: Callback on state transitions. Signature: (old_state, new_state).
        """
        self._sink = sink
        self._fallback = fallback
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._on_state_change = on_state_change
        
        self._lock = threading.Lock()
        self._state = "closed"
        self._failure_count = 0
        self._last_failure_time: Optional[float] = None
        self._success_count = 0
        self._fallback_count = 0

    def _transition(self, new_state: str) -> None:
        """Transition to a new state, calling callback if provided."""
        old_state = self._state
        if old_state != new_state:
            self._state = new_state
            if self._on_state_change:
                try:
                    self._on_state_change(old_state, new_state)
                except Exception:
                    pass

    def send(self, event: Dict[str, Any], tags: Dict[str, Any]) -> None:
        import time
        
        with self._lock:
            current_state = self._state
            
            # Check if we should transition from open to half-open
            if current_state == "open" and self._last_failure_time:
                if time.time() - self._last_failure_time >= self._recovery_timeout:
                    self._transition("half_open")
                    current_state = "half_open"
        
        if current_state == "closed" or current_state == "half_open":
            try:
                self._sink.send(event, tags)
                with self._lock:
                    self._success_count += 1
                    if current_state == "half_open":
                        # Recovery successful
                        self._failure_count = 0
                        self._transition("closed")
            except Exception:
                with self._lock:
                    self._failure_count += 1
                    self._last_failure_time = time.time()
                    if self._failure_count >= self._failure_threshold:
                        self._transition("open")
                # Use fallback if available
                if self._fallback:
                    with self._lock:
                        self._fallback_count += 1
                    self._fallback.send(event, tags)
                else:
                    raise
        else:  # open
            if self._fallback:
                with self._lock:
                    self._fallback_count += 1
                self._fallback.send(event, tags)
            # If no fallback, silently drop (or could raise)

    @property
    def state(self) -> str:
        """Current circuit state: 'closed', 'open', or 'half_open'."""
        with self._lock:
            return self._state

    @property
    def fallback_count(self) -> int:
        """Number of events sent to fallback."""
        with self._lock:
            return self._fallback_count

    def reset(self) -> None:
        """Manually reset the circuit to closed state."""
        with self._lock:
            self._transition("closed")
            self._failure_count = 0
            self._last_failure_time = None


# Default ruleset used when no ruleset is provided or loading fails
DEFAULT_RULESET: Dict[str, Any] = {
    "profile_name": "default-fallback",
    "mode": "monitor",
    "rules": [],
}


class CerbiQueueHandler(logging.Handler):
    """A handler that applies governance and queues events for async processing.

    This handler implements the same governance pattern as CerbiStream, Mel, and
    other Cerbi ecosystem plugins. Events are evaluated against the ruleset,
    governance tags and scoring are applied, then events are passed to a
    background worker that forwards them to a configurable sink.

    The queue-based architecture provides:
    - Non-blocking logging (events are queued, not processed synchronously)
    - Background processing via a dedicated worker thread
    - Pluggable sinks (in-memory, callback, or custom implementations)
    - Graceful shutdown with configurable timeout
    - Real-time governance based on JSON rulesets with hot reload
    - Enterprise observability via metrics and callbacks

    Example:
        >>> sink = InMemoryQueueSink()
        >>> handler = CerbiQueueHandler(
        ...     ruleset_path="/path/to/ruleset.json",
        ...     sink=sink,
        ...     default_app_name="my-service",
        ...     default_environment="prod",
        ...     on_drop=lambda e, t: alert("Event dropped due to backpressure"),
        ... )
        >>> logging.getLogger("app").addHandler(handler)
        >>> # Monitor health
        >>> print(handler.metrics.snapshot())
    """

    def __init__(
        self,
        ruleset: Optional[dict[str, Any]] = None,
        ruleset_path: Optional[str] = None,
        sink: Optional[QueueSink] = None,
        level: int = logging.NOTSET,
        *,
        default_app_name: Optional[str] = None,
        default_environment: Optional[str] = None,
        stringify_collections: bool = False,
        queue_size: int = 10000,
        shutdown_timeout: float = 5.0,
        event_id_factory: Optional[Callable[[], str]] = None,
        time_provider: Optional[Callable[[], str]] = None,
        on_drop: Optional[Callable[[Dict[str, Any], Dict[str, Any]], None]] = None,
        on_sink_error: Optional[Callable[[Exception, Dict[str, Any], Dict[str, Any]], None]] = None,
        high_performance: bool = False,
    ):
        """Initialize the queue handler.

        Args:
            ruleset: A governance ruleset dict (mutually exclusive with ruleset_path).
            ruleset_path: Path to a JSON ruleset file with hot reload support.
            sink: A QueueSink implementation to receive governed events.
            level: Logging level threshold.
            default_app_name: Default AppName for scoring identity.
            default_environment: Default Environment for scoring identity.
            stringify_collections: JSON-encode lists/dicts for string-only sinks.
            queue_size: Maximum queue depth before blocking (default 10000).
            shutdown_timeout: Seconds to wait for queue drain on shutdown.
            event_id_factory: Optional callable to generate CerbiEventId values.
            time_provider: Optional callable to generate CerbiEventTimeUtc values.
            on_drop: Callback invoked when an event is dropped due to queue full.
                     Signature: (event, tags) -> None. Use for alerting.
            on_sink_error: Callback invoked when sink.send() raises an exception.
                           Signature: (exception, event, tags) -> None. Use for DLQ.
            high_performance: Enable optimized ID/timestamp generation for ~2x throughput.
                              Trade-off: IDs are sequential (not UUIDs), timestamps cached 100ms.
        """
        super().__init__(level=level)
        self.loader = RulesetLoader(ruleset=ruleset, ruleset_path=ruleset_path)
        self._sink = sink or InMemoryQueueSink()
        self._default_app_name = default_app_name
        self._default_environment = default_environment
        self._stringify_collections = stringify_collections
        self._event_id_factory = event_id_factory
        self._time_provider = time_provider
        self._shutdown_timeout = shutdown_timeout
        self._on_drop = on_drop
        self._on_sink_error = on_sink_error
        self._high_performance = high_performance

        # Enterprise metrics
        self._metrics = QueueHandlerMetrics()

        # Thread-safe queue for async processing
        self._queue: queue.Queue[Optional[tuple[Dict[str, Any], Dict[str, Any]]]] = queue.Queue(
            maxsize=queue_size
        )

        # Background worker thread
        self._shutdown_event = threading.Event()
        self._worker = threading.Thread(target=self._process_queue, daemon=True, name="CerbiQueueWorker")
        self._worker.start()

        # Register shutdown handler
        atexit.register(self.shutdown)

    def _build_event_dict(self, record: logging.LogRecord) -> Dict[str, Any]:
        """Build a structured event from a LogRecord including extras."""
        excluded = {
            "exc_info",
            "exc_text",
            "stack_info",
            "args",
            "created",
            "msecs",
            "relativeCreated",
            "thread",
            "threadName",
            "process",
            "processName",
            "module",
            "funcName",
            "filename",
            "pathname",
            "lineno",
            "event",
        }
        event: Dict[str, Any] = {}
        for key, value in record.__dict__.items():
            if key in excluded:
                continue
            if key == "msg":
                event["message"] = record.getMessage()
            else:
                event[key] = value

        extra_event = record.__dict__.get("event")
        if isinstance(extra_event, dict):
            event.update(extra_event)
        return event

    def _process_queue(self) -> None:
        """Background worker that processes queued events."""
        while True:
            try:
                item = self._queue.get(timeout=0.1)
                if item is None:  # Poison pill for shutdown
                    self._queue.task_done()
                    break
                event, tags = item
                try:
                    self._sink.send(event, tags)
                    self._metrics._inc_processed()
                except Exception as exc:
                    self._metrics._inc_sink_error()
                    if self._on_sink_error:
                        try:
                            self._on_sink_error(exc, event, tags)
                        except Exception:
                            pass  # Don't let callback errors propagate
                finally:
                    self._queue.task_done()
            except queue.Empty:
                if self._shutdown_event.is_set():
                    # Shutdown requested and queue is empty
                    break
                continue

    def emit(self, record: logging.LogRecord) -> None:
        """Apply governance and queue the event for async processing."""
        try:
            self._metrics._inc_emitted()
            event = self._build_event_dict(record)
            ruleset, error = self.loader.get_ruleset()

            governed_event, tags = evaluate_event(
                event,
                ruleset,
                config_error=error,
                default_app_name=self._default_app_name,
                default_environment=self._default_environment,
                event_id_factory=self._event_id_factory,
                time_provider=self._time_provider,
                stringify_collections=self._stringify_collections,
                high_performance=self._high_performance,
            )

            # Attach governance metadata to the record for other handlers
            record.cerbi_event = governed_event
            for key, value in tags.items():
                setattr(record, key, value)

            # Queue for async processing - non-blocking put with timeout
            try:
                self._queue.put_nowait((governed_event, tags))
            except queue.Full:
                # Queue is full; drop event to avoid blocking logging
                self._metrics._inc_dropped()
                if self._on_drop:
                    try:
                        self._on_drop(governed_event, tags)
                    except Exception:
                        pass  # Don't let callback errors propagate

        except Exception:
            self._metrics._inc_governance_error()

    @property
    def metrics(self) -> QueueHandlerMetrics:
        """Return the metrics tracker for observability."""
        return self._metrics

    def shutdown(self, timeout: Optional[float] = None) -> None:
        """Gracefully shutdown the queue handler.

        Args:
            timeout: Seconds to wait for queue drain. Uses shutdown_timeout if None.
        """
        if self._shutdown_event.is_set():
            return

        timeout = timeout if timeout is not None else self._shutdown_timeout

        # Wait for queue to drain before signaling shutdown
        try:
            self._queue.join()
        except Exception:
            pass

        # Signal shutdown and send poison pill to stop worker
        self._shutdown_event.set()
        try:
            self._queue.put(None, timeout=1.0)
        except queue.Full:
            pass

        # Wait for worker to finish
        self._worker.join(timeout=timeout)

    def close(self) -> None:
        """Close the handler and shutdown the queue."""
        self.shutdown()
        super().close()

    @property
    def sink(self) -> QueueSink:
        """Return the configured sink."""
        return self._sink

    @property
    def pending_count(self) -> int:
        """Return the approximate number of pending events in the queue."""
        return self._queue.qsize()

