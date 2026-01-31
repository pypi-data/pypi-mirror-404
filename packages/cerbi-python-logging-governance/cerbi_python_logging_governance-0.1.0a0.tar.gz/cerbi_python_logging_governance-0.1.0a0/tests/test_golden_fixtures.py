import json
import logging
from pathlib import Path

from cerbi_python_logging_governance.filter import CerbiGovernanceFilter

FIXTURE_ROOT = Path(__file__).resolve().parents[1] / "golden-fixtures"


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def build_record(name: str, level: str, msg: str, extra: dict):
    levelno = logging._nameToLevel.get(level.upper(), logging.INFO)
    record = logging.LogRecord(name, levelno, pathname="fixture", lineno=0, msg=msg, args=(), exc_info=None, func=None, sinfo=None)
    for key, value in (extra or {}).items():
        setattr(record, key, value)
    return record


def assert_events_match(actual: dict, expected: dict):
    assert actual == expected


def test_golden_fixtures():
    event_id = "00000000-0000-0000-0000-000000000000"
    event_time = "2024-01-01T00:00:00+00:00"
    for fixture_dir in sorted(p for p in FIXTURE_ROOT.iterdir() if p.is_dir()):
        ruleset = load_json(fixture_dir / "ruleset.json")
        incoming = load_json(fixture_dir / "event_in.json")
        expected = load_json(fixture_dir / "event_out.json")

        record = build_record(
            incoming["name"], incoming["level"], incoming["msg"], incoming.get("extra", {})
        )

        governance_filter = CerbiGovernanceFilter(
            ruleset=ruleset,
            default_app_name="fixture-app",
            default_environment="test",
            event_id_factory=lambda: event_id,
            time_provider=lambda: event_time,
        )
        governance_filter.filter(record)

        assert_events_match(record.cerbi_event, expected)
