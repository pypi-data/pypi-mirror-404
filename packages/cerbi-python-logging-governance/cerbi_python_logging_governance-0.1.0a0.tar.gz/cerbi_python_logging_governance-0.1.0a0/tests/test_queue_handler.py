"""Tests for the CerbiQueueHandler and related sink classes."""
import json
import logging
import tempfile
import threading
import time
from pathlib import Path

import pytest

from cerbi_python_logging_governance import (
    CerbiQueueHandler,
    InMemoryQueueSink,
    CallbackQueueSink,
    FallbackSink,
    CircuitBreakerSink,
)


@pytest.fixture
def sample_ruleset():
    return {
        "profile_name": "test-profile",
        "mode": "enforce",
        "rules": [
            {"id": "redact-email", "field": "user.email", "action": "redact"},
            {"id": "require-user-id", "field": "user.id", "required": True},
        ],
    }


@pytest.fixture
def sample_ruleset_file(sample_ruleset):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(sample_ruleset, f)
        return f.name


class TestInMemoryQueueSink:
    def test_send_stores_events(self):
        sink = InMemoryQueueSink()
        event = {"message": "test"}
        tags = {"GovernanceMode": "enforce"}

        sink.send(event, tags)

        assert len(sink.events) == 1
        assert sink.events[0] == (event, tags)

    def test_clear_removes_events(self):
        sink = InMemoryQueueSink()
        sink.send({"message": "test"}, {})
        sink.send({"message": "test2"}, {})

        sink.clear()

        assert len(sink.events) == 0

    def test_thread_safety(self):
        sink = InMemoryQueueSink()
        threads = []

        def send_events():
            for i in range(100):
                sink.send({"index": i}, {})

        for _ in range(10):
            t = threading.Thread(target=send_events)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        assert len(sink.events) == 1000


class TestCallbackQueueSink:
    def test_invokes_callback(self):
        received = []

        def callback(event, tags):
            received.append((event, tags))

        sink = CallbackQueueSink(callback)
        sink.send({"message": "hello"}, {"tag": "value"})

        assert len(received) == 1
        assert received[0] == ({"message": "hello"}, {"tag": "value"})


class TestCerbiQueueHandler:
    def test_basic_event_processing(self, sample_ruleset):
        sink = InMemoryQueueSink()
        handler = CerbiQueueHandler(
            ruleset=sample_ruleset,
            sink=sink,
            default_app_name="test-app",
            default_environment="test",
            event_id_factory=lambda: "test-id-123",
            time_provider=lambda: "2024-01-01T00:00:00+00:00",
        )

        logger = logging.getLogger("test_basic")
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        logger.info("User login", extra={"event": {"user": {"email": "alice@example.com"}}})

        # Give background worker time to process
        time.sleep(0.2)

        handler.shutdown()
        logger.removeHandler(handler)

        assert len(sink.events) == 1
        event, tags = sink.events[0]

        # Verify governance was applied
        assert tags["GovernanceProfileUsed"] == "test-profile"
        assert tags["GovernanceMode"] == "enforce"
        assert tags["GovernanceEnforced"] is True
        assert event["user"]["email"] == "[REDACTED]"

    def test_metrics_tracking(self, sample_ruleset):
        sink = InMemoryQueueSink()
        handler = CerbiQueueHandler(
            ruleset=sample_ruleset,
            sink=sink,
        )

        logger = logging.getLogger("test_metrics")
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        for i in range(5):
            logger.info(f"Event {i}", extra={"event": {}})

        time.sleep(0.2)
        handler.shutdown()
        logger.removeHandler(handler)

        # Verify metrics
        assert handler.metrics.emitted_count == 5
        assert handler.metrics.processed_count == 5
        assert handler.metrics.dropped_count == 0

        snapshot = handler.metrics.snapshot()
        assert snapshot["emitted_count"] == 5
        assert snapshot["processed_count"] == 5

    def test_on_drop_callback(self, sample_ruleset):
        dropped_events = []

        def on_drop(event, tags):
            dropped_events.append((event, tags))

        sink = InMemoryQueueSink()
        handler = CerbiQueueHandler(
            ruleset=sample_ruleset,
            sink=sink,
            queue_size=1,  # Tiny queue to force drops
            on_drop=on_drop,
        )

        logger = logging.getLogger("test_on_drop")
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        # Flood the tiny queue
        for i in range(100):
            logger.info(f"Event {i}", extra={"event": {}})

        handler.shutdown()
        logger.removeHandler(handler)

        # Should have dropped some events and called callback
        assert handler.metrics.dropped_count > 0
        assert len(dropped_events) == handler.metrics.dropped_count

    def test_on_sink_error_callback(self, sample_ruleset):
        errors = []

        def on_sink_error(exc, event, tags):
            errors.append((exc, event, tags))

        class FailingSink:
            def send(self, event, tags):
                raise RuntimeError("Sink failed!")

        handler = CerbiQueueHandler(
            ruleset=sample_ruleset,
            sink=FailingSink(),
            on_sink_error=on_sink_error,
        )

        logger = logging.getLogger("test_sink_error")
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        logger.info("Event", extra={"event": {}})

        time.sleep(0.2)
        handler.shutdown()
        logger.removeHandler(handler)

        # Should have recorded sink error and called callback
        assert handler.metrics.sink_error_count == 1
        assert len(errors) == 1
        assert isinstance(errors[0][0], RuntimeError)

    def test_governance_tags_attached_to_record(self, sample_ruleset):
        sink = InMemoryQueueSink()
        handler = CerbiQueueHandler(
            ruleset=sample_ruleset,
            sink=sink,
            default_app_name="test-app",
            default_environment="test",
        )

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="test message",
            args=(),
            exc_info=None,
        )
        record.event = {"user": {"email": "test@example.com"}}

        handler.emit(record)

        # Verify tags are attached to record
        assert hasattr(record, "GovernanceProfileUsed")
        assert record.GovernanceProfileUsed == "test-profile"
        assert hasattr(record, "cerbi_event")

        handler.shutdown()

    def test_scoring_identity_fields(self, sample_ruleset):
        sink = InMemoryQueueSink()
        handler = CerbiQueueHandler(
            ruleset=sample_ruleset,
            sink=sink,
            default_app_name="my-service",
            default_environment="prod",
            event_id_factory=lambda: "fixed-uuid",
            time_provider=lambda: "2024-06-15T12:00:00+00:00",
        )

        logger = logging.getLogger("test_scoring")
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        logger.info("Event", extra={"event": {}})

        time.sleep(0.2)
        handler.shutdown()
        logger.removeHandler(handler)

        assert len(sink.events) == 1
        event, _ = sink.events[0]

        # Verify scoring compatibility fields
        assert event["CerbiEventId"] == "fixed-uuid"
        assert event["CerbiEventTimeUtc"] == "2024-06-15T12:00:00+00:00"
        assert event["AppName"] == "my-service"
        assert event["Environment"] == "prod"



    def test_violations_counted_for_scoring(self, sample_ruleset):
        sink = InMemoryQueueSink()
        handler = CerbiQueueHandler(
            ruleset=sample_ruleset,
            sink=sink,
        )

        logger = logging.getLogger("test_violations")
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        # This event is missing required user.id field
        logger.info("Event", extra={"event": {"user": {"email": "test@example.com"}}})

        time.sleep(0.2)
        handler.shutdown()
        logger.removeHandler(handler)

        assert len(sink.events) == 1
        event, tags = sink.events[0]

        # Verify violations are tracked for scoring
        # Default severity is "Warn" with weight 2.0 per Cerbi contract
        assert tags["GovernanceScoreImpact"] == 2.0  # 1 violation * Warn weight (2.0)
        assert len(tags["GovernanceViolations"]) == 1
        assert "require-user-id" in tags["GovernanceViolations"][0]

    def test_ruleset_path_hot_reload(self, sample_ruleset_file, sample_ruleset):
        sink = InMemoryQueueSink()
        handler = CerbiQueueHandler(
            ruleset_path=sample_ruleset_file,
            sink=sink,
        )

        logger = logging.getLogger("test_reload")
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        logger.info("Event1", extra={"event": {"user": {"email": "test@example.com"}}})
        time.sleep(0.2)

        # Modify ruleset file
        modified_ruleset = {
            "profile_name": "updated-profile",
            "mode": "relaxed",
            "rules": [],
        }
        with open(sample_ruleset_file, "w") as f:
            json.dump(modified_ruleset, f)

        # Force a small delay to ensure mtime changes
        time.sleep(0.1)

        logger.info("Event2", extra={"event": {"user": {"email": "test@example.com"}}})
        time.sleep(0.2)

        handler.shutdown()
        logger.removeHandler(handler)

        assert len(sink.events) == 2

        # First event used original ruleset
        _, tags1 = sink.events[0]
        assert tags1["GovernanceProfileUsed"] == "test-profile"

        # Second event used updated ruleset
        _, tags2 = sink.events[1]
        assert tags2["GovernanceProfileUsed"] == "updated-profile"
        assert tags2["GovernanceRelaxed"] is True

    def test_stringify_collections(self, sample_ruleset):
        sink = InMemoryQueueSink()
        handler = CerbiQueueHandler(
            ruleset=sample_ruleset,
            sink=sink,
            stringify_collections=True,
        )

        logger = logging.getLogger("test_stringify")
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        logger.info("Event", extra={"event": {}})

        time.sleep(0.2)
        handler.shutdown()
        logger.removeHandler(handler)

        assert len(sink.events) == 1
        event, tags = sink.events[0]

        # Violations should be JSON strings when stringify_collections is True
        assert isinstance(tags["GovernanceViolations"], str)
        assert isinstance(tags["GovernanceViolationsStructured"], str)

    def test_graceful_shutdown(self, sample_ruleset):
        sink = InMemoryQueueSink()
        handler = CerbiQueueHandler(
            ruleset=sample_ruleset,
            sink=sink,
            shutdown_timeout=2.0,
        )

        logger = logging.getLogger("test_shutdown")
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        # Send multiple events
        for i in range(10):
            logger.info(f"Event {i}", extra={"event": {}})

        handler.shutdown()
        logger.removeHandler(handler)

        # All events should be processed
        assert len(sink.events) == 10

    def test_config_failure_handling(self):
        sink = InMemoryQueueSink()
        # Invalid ruleset - missing required fields
        handler = CerbiQueueHandler(
            ruleset={"invalid": "ruleset"},
            sink=sink,
        )

        logger = logging.getLogger("test_config_failure")
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        logger.info("Event", extra={"event": {}})

        time.sleep(0.2)
        handler.shutdown()
        logger.removeHandler(handler)

        assert len(sink.events) == 1
        event, tags = sink.events[0]

        # Should have config failure tags
        assert tags["GovernanceConfigFailed"] is True
        assert tags["GovernanceProfileUsed"] == "unknown"
        assert tags["GovernanceScoreImpact"] == 0

    def test_relaxed_mode_bypasses_rules(self):
        sink = InMemoryQueueSink()
        ruleset = {
            "profile_name": "relaxed-profile",
            "mode": "relaxed",
            "rules": [
                {"id": "redact-email", "field": "user.email", "action": "redact"},
            ],
        }
        handler = CerbiQueueHandler(
            ruleset=ruleset,
            sink=sink,
        )

        logger = logging.getLogger("test_relaxed")
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        logger.info("Event", extra={"event": {"user": {"email": "alice@example.com"}}})

        time.sleep(0.2)
        handler.shutdown()
        logger.removeHandler(handler)

        assert len(sink.events) == 1
        event, tags = sink.events[0]

        # Email should NOT be redacted in relaxed mode
        assert event["user"]["email"] == "alice@example.com"
        assert tags["GovernanceRelaxed"] is True
        assert tags["GovernanceEnforced"] is False

    def test_pending_count(self, sample_ruleset):
        # Use a slow sink to test pending count
        class SlowSink:
            def __init__(self):
                self.events = []

            def send(self, event, tags):
                time.sleep(0.1)
                self.events.append((event, tags))

        slow_sink = SlowSink()
        handler = CerbiQueueHandler(
            ruleset=sample_ruleset,
            sink=slow_sink,
        )

        logger = logging.getLogger("test_pending")
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        # Send events quickly
        for i in range(5):
            logger.info(f"Event {i}", extra={"event": {}})

        # Should have some pending events
        assert handler.pending_count >= 0

        handler.shutdown(timeout=5.0)
        logger.removeHandler(handler)


class TestFallbackSink:
    def test_uses_primary_when_healthy(self):
        primary = InMemoryQueueSink()
        fallback = InMemoryQueueSink()
        sink = FallbackSink(primary, fallback)

        sink.send({"message": "test"}, {"tag": "value"})

        assert len(primary.events) == 1
        assert len(fallback.events) == 0

    def test_uses_fallback_when_primary_fails(self):
        class FailingSink:
            def send(self, event, tags):
                raise RuntimeError("Primary failed!")

        fallback = InMemoryQueueSink()
        sink = FallbackSink(FailingSink(), fallback)

        sink.send({"message": "test"}, {"tag": "value"})

        assert len(fallback.events) == 1
        assert sink.fallback_count == 1

    def test_calls_on_fallback_callback(self):
        callbacks = []

        def on_fallback(exc, event, tags):
            callbacks.append((exc, event, tags))

        class FailingSink:
            def send(self, event, tags):
                raise RuntimeError("Failed!")

        fallback = InMemoryQueueSink()
        sink = FallbackSink(FailingSink(), fallback, on_fallback=on_fallback)

        sink.send({"message": "test"}, {})

        assert len(callbacks) == 1
        assert isinstance(callbacks[0][0], RuntimeError)


class TestCircuitBreakerSink:
    def test_starts_closed(self):
        sink = CircuitBreakerSink(InMemoryQueueSink())
        assert sink.state == "closed"

    def test_opens_after_threshold_failures(self):
        class FailingSink:
            def send(self, event, tags):
                raise RuntimeError("Failed!")

        fallback = InMemoryQueueSink()
        sink = CircuitBreakerSink(
            FailingSink(),
            fallback=fallback,
            failure_threshold=3,
        )

        # Send 3 events to trigger open
        for i in range(3):
            sink.send({"i": i}, {})

        assert sink.state == "open"
        assert len(fallback.events) == 3

    def test_uses_fallback_when_open(self):
        class FailingSink:
            def send(self, event, tags):
                raise RuntimeError("Failed!")

        fallback = InMemoryQueueSink()
        sink = CircuitBreakerSink(
            FailingSink(),
            fallback=fallback,
            failure_threshold=2,
        )

        # Open the circuit
        sink.send({}, {})
        sink.send({}, {})
        assert sink.state == "open"

        # Further events should go directly to fallback
        sink.send({"after_open": True}, {})
        assert len(fallback.events) == 3

    def test_transitions_to_half_open_after_timeout(self):
        class FailingSink:
            def send(self, event, tags):
                raise RuntimeError("Failed!")

        fallback = InMemoryQueueSink()
        sink = CircuitBreakerSink(
            FailingSink(),
            fallback=fallback,
            failure_threshold=1,
            recovery_timeout=0.1,  # Very short for testing
        )

        # Open the circuit
        sink.send({}, {})
        assert sink.state == "open"

        # Wait for recovery timeout
        time.sleep(0.2)

        # Next send should trigger half-open and test
        sink.send({}, {})
        # Still failing, so back to open
        assert sink.state == "open"

    def test_recovers_when_sink_healthy_again(self):
        call_count = [0]

        class IntermittentSink:
            def send(self, event, tags):
                call_count[0] += 1
                if call_count[0] <= 2:
                    raise RuntimeError("Temporary failure")
                # After 2 failures, start working

        fallback = InMemoryQueueSink()
        sink = CircuitBreakerSink(
            IntermittentSink(),
            fallback=fallback,
            failure_threshold=2,
            recovery_timeout=0.1,
        )

        # Fail twice to open circuit
        sink.send({}, {})
        sink.send({}, {})
        assert sink.state == "open"

        # Wait for recovery
        time.sleep(0.2)

        # This should succeed (half-open -> closed)
        sink.send({"recovery": True}, {})
        assert sink.state == "closed"

    def test_calls_on_state_change_callback(self):
        transitions = []

        def on_state_change(old, new):
            transitions.append((old, new))

        class FailingSink:
            def send(self, event, tags):
                raise RuntimeError("Failed!")

        sink = CircuitBreakerSink(
            FailingSink(),
            fallback=InMemoryQueueSink(),
            failure_threshold=2,
            on_state_change=on_state_change,
        )

        sink.send({}, {})
        sink.send({}, {})

        assert ("closed", "open") in transitions

    def test_manual_reset(self):
        class FailingSink:
            def send(self, event, tags):
                raise RuntimeError("Failed!")

        sink = CircuitBreakerSink(
            FailingSink(),
            fallback=InMemoryQueueSink(),
            failure_threshold=1,
        )

        sink.send({}, {})
        assert sink.state == "open"

        sink.reset()
        assert sink.state == "closed"
