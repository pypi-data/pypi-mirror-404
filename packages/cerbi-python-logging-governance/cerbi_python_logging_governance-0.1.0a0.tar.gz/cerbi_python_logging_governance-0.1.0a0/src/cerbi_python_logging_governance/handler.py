"""Logging handler that applies governance before delegating."""
from __future__ import annotations

import logging
from typing import Any, Optional

from .filter import CerbiGovernanceFilter
from .loader import RulesetLoader


class CerbiGovernanceHandler(logging.Handler):
    """A handler that injects governance metadata then forwards to a delegate."""

    def __init__(
        self,
        ruleset: Optional[dict[str, Any]] = None,
        ruleset_path: Optional[str] = None,
        delegate: Optional[logging.Handler] = None,
        level: int = logging.NOTSET,
        *,
        default_app_name: Optional[str] = None,
        default_environment: Optional[str] = None,
        stringify_collections: bool = False,
    ):
        super().__init__(level=level)
        self.loader = RulesetLoader(ruleset=ruleset, ruleset_path=ruleset_path)
        self._filter = CerbiGovernanceFilter(
            loader=self.loader,
            default_app_name=default_app_name,
            default_environment=default_environment,
            stringify_collections=stringify_collections,
        )
        self.delegate = delegate or logging.StreamHandler()

    def emit(self, record: logging.LogRecord) -> None:  # type: ignore[override]
        # Apply governance inline; swallow errors to avoid blocking logging.
        try:
            self._filter.filter(record)
        except Exception:
            pass
        self.delegate.emit(record)
