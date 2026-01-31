"""Data models used by the governance evaluator."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


# Default severity weights matching Cerbi.Governance.Core contract
# Severities: Info, Warn, Error (not critical/high/medium/low)
DEFAULT_SEVERITY_WEIGHTS: dict[str, float] = {
    "Info": 0.5,
    "Warn": 2.0,
    "Error": 5.0,
}


@dataclass
class Violation:
    """A governance violation with severity and weight for scoring."""
    rule_id: str
    field: str
    reason: str
    severity: str = "Warn"  # Info, Warn, Error
    weight: float = 2.0  # Default to Warn weight

    def as_summary(self) -> str:
        return f"{self.rule_id}: {self.reason}"

    def as_structured(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "field": self.field,
            "reason": self.reason,
            "severity": self.severity,
            "weight": self.weight,
        }


@dataclass
class ScoringConfig:
    """Configuration for weighted scoring per Cerbi.Governance.Core contract.
    
    Matches the ScoringSettings model from Cerbi.Governance.Core:
    - enabled: bool
    - weightsBySeverity: {"Info": 0.5, "Warn": 2.0, "Error": 5.0}
    - pluginWeights: {"ruleId": weight} for rule-specific overrides
    - version: semver string (default "1.0.0")
    
    Example in ruleset.json:
        {
            "profile_name": "default",
            "mode": "enforce",
            "scoring": {
                "enabled": true,
                "weightsBySeverity": {"Info": 0.5, "Warn": 2.0, "Error": 5.0},
                "pluginWeights": {"pii-email": 3.0, "require-user-id": 5.0},
                "version": "1.0.0"
            },
            "rules": [
                {"id": "pii-email", "field": "user.email", "action": "redact", "severity": "Error"},
                {"id": "require-user-id", "field": "user.id", "required": true, "severity": "Error"}
            ]
        }
    """
    enabled: bool = True
    weights_by_severity: dict[str, float] = field(default_factory=lambda: DEFAULT_SEVERITY_WEIGHTS.copy())
    plugin_weights: dict[str, float] = field(default_factory=dict)  # ruleId -> weight override
    version: str = "1.0.0"
    
    @classmethod
    def from_dict(cls, data: Optional[dict[str, Any]]) -> "ScoringConfig":
        """Create ScoringConfig from dict (e.g., from JSON).
        
        Supports both Python snake_case and JSON camelCase keys for compatibility.
        """
        if not data:
            return cls()
        
        # Support both camelCase (JSON) and snake_case (Python)
        weights = data.get("weightsBySeverity") or data.get("weights_by_severity") or {}
        plugin_weights = data.get("pluginWeights") or data.get("plugin_weights") or {}
        
        return cls(
            enabled=data.get("enabled", True),
            weights_by_severity={**DEFAULT_SEVERITY_WEIGHTS, **weights},
            plugin_weights=plugin_weights,
            version=data.get("version", "1.0.0"),
        )
    
    def get_weight_for_rule(self, rule_id: str, severity: str) -> float:
        """Get weight for a rule, checking pluginWeights first, then severity weights."""
        # Plugin weight takes precedence if defined
        if rule_id in self.plugin_weights:
            return self.plugin_weights[rule_id]
        # Fall back to severity weight
        return self.weights_by_severity.get(severity, DEFAULT_SEVERITY_WEIGHTS.get("Warn", 2.0))
