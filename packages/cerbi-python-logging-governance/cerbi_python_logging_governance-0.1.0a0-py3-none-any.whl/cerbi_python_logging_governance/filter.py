"""Logging filter that applies Cerbi governance."""
from __future__ import annotations

import logging
from typing import Any, Callable, Dict, Optional

from .evaluator import evaluate_event
from .loader import RulesetLoader


def build_event_dict(record: logging.LogRecord) -> Dict[str, Any]:
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


class CerbiGovernanceFilter(logging.Filter):
    """Inject governance tags into a record and attach the governed event."""

    def __init__(
        self,
        name: str = "",
        ruleset: Optional[dict[str, Any]] = None,
        ruleset_path: Optional[str] = None,
        loader: Optional[RulesetLoader] = None,
        *,
        default_app_name: Optional[str] = None,
        default_environment: Optional[str] = None,
        event_id_factory: Optional[Callable[[], str]] = None,
        time_provider: Optional[Callable[[], str]] = None,
        stringify_collections: bool = False,
    ):
        super().__init__(name)
        self.loader = loader or RulesetLoader(ruleset=ruleset, ruleset_path=ruleset_path)
        self._default_app_name = default_app_name
        self._default_environment = default_environment
        self._event_id_factory = event_id_factory
        self._time_provider = time_provider
        self._stringify_collections = stringify_collections

    def filter(self, record: logging.LogRecord) -> bool:  # type: ignore[override]
        event = build_event_dict(record)
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
        )

        record.cerbi_event = governed_event
        for key, value in tags.items():
            setattr(record, key, value)
        return True

