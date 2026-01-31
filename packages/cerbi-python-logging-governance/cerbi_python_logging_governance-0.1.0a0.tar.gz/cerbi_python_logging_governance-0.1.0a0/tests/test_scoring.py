"""Tests for weighted scoring functionality per Cerbi.Governance.Core contract."""
import logging
import time

import pytest

from cerbi_python_logging_governance import (
    CerbiQueueHandler,
    InMemoryQueueSink,
    ScoringConfig,
    DEFAULT_SEVERITY_WEIGHTS,
)


class TestWeightedScoring:
    def test_default_severity_weights(self):
        """Verify default severity weights match Cerbi contract (Info/Warn/Error)."""
        assert DEFAULT_SEVERITY_WEIGHTS == {
            "Info": 0.5,
            "Warn": 2.0,
            "Error": 5.0,
        }

    def test_scoring_config_from_dict_camelcase(self):
        """Test ScoringConfig.from_dict() with camelCase keys (JSON format)."""
        config = ScoringConfig.from_dict({
            "enabled": True,
            "weightsBySeverity": {"Error": 10.0, "Warn": 3.0},
            "pluginWeights": {"my-rule": 7.5},
            "version": "2.0.0",
        })
        
        assert config.enabled is True
        assert config.weights_by_severity["Error"] == 10.0
        assert config.weights_by_severity["Warn"] == 3.0
        assert config.weights_by_severity["Info"] == 0.5  # Default preserved
        assert config.plugin_weights["my-rule"] == 7.5
        assert config.version == "2.0.0"

    def test_scoring_config_plugin_weight_override(self):
        """Test that pluginWeights override severity weights for specific rules."""
        config = ScoringConfig.from_dict({
            "weightsBySeverity": {"Error": 5.0},
            "pluginWeights": {"special-rule": 100.0},
        })
        
        # Rule with plugin weight
        assert config.get_weight_for_rule("special-rule", "Error") == 100.0
        
        # Rule without plugin weight falls back to severity
        assert config.get_weight_for_rule("other-rule", "Error") == 5.0

    def test_weighted_scoring_in_ruleset(self):
        """Test that severity in rules affects GovernanceScoreImpact per contract."""
        ruleset = {
            "profile_name": "weighted-test",
            "mode": "enforce",
            "scoring": {
                "enabled": True,
                "weightsBySeverity": {
                    "Info": 0.5,
                    "Warn": 2.0,
                    "Error": 5.0,
                },
                "version": "1.0.0",
            },
            "rules": [
                {"id": "error-rule", "field": "user.id", "required": True, "severity": "Error"},
                {"id": "warn-rule", "field": "user.email", "required": True, "severity": "Warn"},
                {"id": "info-rule", "field": "user.name", "required": True, "severity": "Info"},
            ],
        }
        
        sink = InMemoryQueueSink()
        handler = CerbiQueueHandler(ruleset=ruleset, sink=sink)
        
        logger = logging.getLogger("test_weighted")
        logger.handlers = []
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        
        # Log event missing all required fields
        logger.info("Test", extra={"event": {}})
        
        time.sleep(0.2)
        handler.shutdown()
        logger.removeHandler(handler)
        
        assert len(sink.events) == 1
        event, tags = sink.events[0]
        
        # Score should be: Error(5.0) + Warn(2.0) + Info(0.5) = 7.5
        assert tags["GovernanceScoreImpact"] == 7.5
        
        # Verify GovernanceScoringVersion is present per contract
        assert tags["GovernanceScoringVersion"] == "1.0.0"
        
        # Verify structured violations have severity and weight
        violations = tags["GovernanceViolationsStructured"]
        assert len(violations) == 3
        
        error_violation = next(v for v in violations if v["rule_id"] == "error-rule")
        assert error_violation["severity"] == "Error"
        assert error_violation["weight"] == 5.0

    def test_plugin_weight_override_in_ruleset(self):
        """Test that pluginWeights override severity-based weights."""
        ruleset = {
            "profile_name": "plugin-weight-test",
            "mode": "enforce",
            "scoring": {
                "enabled": True,
                "weightsBySeverity": {"Error": 5.0},
                "pluginWeights": {"special-rule": 25.0},  # Override
            },
            "rules": [
                {"id": "special-rule", "field": "data", "required": True, "severity": "Error"},
            ],
        }
        
        sink = InMemoryQueueSink()
        handler = CerbiQueueHandler(ruleset=ruleset, sink=sink)
        
        logger = logging.getLogger("test_plugin_weight")
        logger.handlers = []
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        
        logger.info("Test", extra={"event": {}})
        
        time.sleep(0.2)
        handler.shutdown()
        logger.removeHandler(handler)
        
        event, tags = sink.events[0]
        
        # Plugin weight (25.0) should override severity weight (5.0)
        assert tags["GovernanceScoreImpact"] == 25.0

    def test_scoring_version_tag(self):
        """Test GovernanceScoringVersion tag is added when scoring enabled."""
        ruleset = {
            "profile_name": "version-test",
            "mode": "enforce",
            "scoring": {
                "enabled": True,
                "version": "2.5.0",
            },
            "rules": [
                {"id": "rule1", "field": "a", "required": True},
            ],
        }
        
        sink = InMemoryQueueSink()
        handler = CerbiQueueHandler(ruleset=ruleset, sink=sink)
        
        logger = logging.getLogger("test_version")
        logger.handlers = []
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        
        logger.info("Test", extra={"event": {}})
        
        time.sleep(0.2)
        handler.shutdown()
        logger.removeHandler(handler)
        
        event, tags = sink.events[0]
        
        assert tags["GovernanceScoringVersion"] == "2.5.0"

    def test_no_violations_zero_score(self):
        """Test that no violations results in zero score."""
        ruleset = {
            "profile_name": "clean",
            "mode": "enforce",
            "scoring": {"enabled": True},
            "rules": [
                {"id": "check-email", "field": "user.email", "required": True, "severity": "Error"},
            ],
        }
        
        sink = InMemoryQueueSink()
        handler = CerbiQueueHandler(ruleset=ruleset, sink=sink)
        
        logger = logging.getLogger("test_clean")
        logger.handlers = []
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        
        # Provide required field
        logger.info("Test", extra={"event": {"user": {"email": "test@example.com"}}})
        
        time.sleep(0.2)
        handler.shutdown()
        logger.removeHandler(handler)
        
        event, tags = sink.events[0]
        
        assert tags["GovernanceScoreImpact"] == 0.0
        assert len(tags["GovernanceViolations"]) == 0

    def test_default_severity_is_warn(self):
        """Test that rules without severity default to Warn (2.0 weight)."""
        ruleset = {
            "profile_name": "default-severity",
            "mode": "enforce",
            "rules": [
                {"id": "no-severity", "field": "data", "required": True},  # No severity specified
            ],
        }
        
        sink = InMemoryQueueSink()
        handler = CerbiQueueHandler(ruleset=ruleset, sink=sink)
        
        logger = logging.getLogger("test_default_severity")
        logger.handlers = []
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        
        logger.info("Test", extra={"event": {}})
        
        time.sleep(0.2)
        handler.shutdown()
        logger.removeHandler(handler)
        
        event, tags = sink.events[0]
        
        # Default severity is Warn with weight 2.0
        assert tags["GovernanceScoreImpact"] == 2.0
        
        violations = tags["GovernanceViolationsStructured"]
        assert violations[0]["severity"] == "Warn"
        assert violations[0]["weight"] == 2.0
