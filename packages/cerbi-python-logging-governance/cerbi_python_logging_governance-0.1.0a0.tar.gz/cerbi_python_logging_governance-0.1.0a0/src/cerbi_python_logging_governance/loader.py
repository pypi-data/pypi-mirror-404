"""Ruleset loading and hot-reload support."""
from __future__ import annotations

import json
import os
import threading
from typing import Any, Optional, Tuple


class RulesetLoader:
    """Loads governance rules either from a dict or a file path with hot reload support."""

    def __init__(self, ruleset: Optional[dict[str, Any]] = None, ruleset_path: Optional[str] = None):
        self._lock = threading.Lock()
        self._ruleset_path = ruleset_path
        self._ruleset = ruleset
        self._last_error: Optional[str] = None
        self._last_mtime: Optional[float] = None
        if ruleset_path:
            self._reload_from_path()

    def _reload_from_path(self) -> None:
        """Attempt to reload from the configured file path."""
        if not self._ruleset_path:
            return
        try:
            mtime = os.path.getmtime(self._ruleset_path)
        except OSError as exc:  # file not found or inaccessible
            with self._lock:
                self._last_error = f"Ruleset file unavailable: {exc}"
            return

        if self._last_mtime is not None and mtime <= self._last_mtime:
            return

        try:
            with open(self._ruleset_path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:  # keep previous ruleset on parse errors
            with self._lock:
                self._last_error = f"Failed to load ruleset: {exc}"
            return

        with self._lock:
            self._ruleset = data
            self._last_mtime = mtime
            self._last_error = None

    def get_ruleset(self) -> Tuple[Optional[dict[str, Any]], Optional[str]]:
        """Return the active ruleset and any configuration error string."""
        if self._ruleset_path:
            self._reload_from_path()
        with self._lock:
            return self._ruleset, self._last_error

