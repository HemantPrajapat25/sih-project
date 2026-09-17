"""
NumberGuard — Risk Rule Engine (Phase 3)

Loads versioned risk rules from the database and evaluates them against
a context dict. Rules can block allocation regardless of score.

Each rule has:
  - code: str (unique identifier)
  - condition_expression: JSON DSL
  - base_weight: int (max points this rule contributes)
  - is_blocking: bool (if True, overrides score → BLOCKED)
  - severity: LOW | MEDIUM | HIGH | CRITICAL
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.models import RiskRule

logger = logging.getLogger("numberguard.risk.rules")


@dataclass
class RuleEvaluation:
    code: str
    name: str
    triggered: bool
    impact: int        # points added (0 if not triggered)
    blocking: bool     # whether this rule forces BLOCKED
    severity: str
    reason: str


class RiskRuleEngine:
    """
    Loads active rules from DB, evaluates each against a context dict.

    Context dict keys expected:
      cooling_completed: bool
      unresolved_critical_providers: int
      fraud_signal: str          (NONE|LOW|MEDIUM|HIGH|CRITICAL)
      spam_signal: str
      all_providers_acknowledged: bool
      recycling_count: int
      otp_services_unlinked: bool
      manual_override_active: bool
      risk_score_before_rules: int
    """

    # Fallback rules used when DB has no active rules yet
    DEFAULT_RULES: List[Dict[str, Any]] = [
        {
            "code": "COOLING_INCOMPLETE",
            "name": "Cooling Period Not Complete",
            "base_weight": 20,
            "is_blocking": True,
            "severity": "HIGH",
            "condition_expression": json.dumps({"field": "cooling_completed", "op": "eq", "value": False}),
        },
        {
            "code": "UNRESOLVED_CRITICAL_PROVIDER",
            "name": "Unresolved Critical Provider Association",
            "base_weight": 20,
            "is_blocking": True,
            "severity": "CRITICAL",
            "condition_expression": json.dumps({"field": "unresolved_critical_providers", "op": "gt", "value": 0}),
        },
        {
            "code": "FRAUD_HIGH",
            "name": "High Fraud Signal",
            "base_weight": 25,
            "is_blocking": False,
            "severity": "CRITICAL",
            "condition_expression": json.dumps({"field": "fraud_signal", "op": "in", "value": ["HIGH", "CRITICAL"]}),
        },
        {
            "code": "SPAM_HIGH",
            "name": "High Spam Reputation",
            "base_weight": 15,
            "is_blocking": False,
            "severity": "HIGH",
            "condition_expression": json.dumps({"field": "spam_signal", "op": "in", "value": ["HIGH", "CRITICAL"]}),
        },
        {
            "code": "ALL_PROVIDERS_ACK",
            "name": "All Providers Acknowledged",
            "base_weight": -20,
            "is_blocking": False,
            "severity": "LOW",
            "condition_expression": json.dumps({"field": "all_providers_acknowledged", "op": "eq", "value": True}),
        },
        {
            "code": "HIGH_RECYCLING",
            "name": "High Recycling Velocity",
            "base_weight": 15,
            "is_blocking": False,
            "severity": "MEDIUM",
            "condition_expression": json.dumps({"field": "recycling_count", "op": "gte", "value": 3}),
        },
        {
            "code": "OTP_SERVICES_PENDING",
            "name": "OTP/Recovery Services Not Unlinked",
            "base_weight": 20,
            "is_blocking": True,
            "severity": "HIGH",
            "condition_expression": json.dumps({"field": "otp_services_unlinked", "op": "eq", "value": False}),
        },
    ]

    def __init__(self, rules: Optional[List[Dict[str, Any]]] = None):
        """
        Pass pre-loaded rules (dicts with code, base_weight, etc.) or None to use defaults.
        """
        self._rules = rules if rules is not None else self.DEFAULT_RULES

    @classmethod
    async def from_db(cls, db: AsyncSession) -> "RiskRuleEngine":
        """Load active rules from the database."""
        try:
            result = await db.execute(
                select(RiskRule).where(RiskRule.is_active == True).order_by(RiskRule.category)
            )
            db_rules = result.scalars().all()
            if db_rules:
                rules = [
                    {
                        "code": r.code,
                        "name": r.name,
                        "base_weight": r.base_weight,
                        "is_blocking": r.is_blocking,
                        "severity": r.severity,
                        "condition_expression": r.condition_expression,
                    }
                    for r in db_rules
                ]
                logger.info(f"Loaded {len(rules)} risk rules from database")
                return cls(rules)
        except Exception as exc:
            logger.warning(f"Could not load rules from DB ({exc}), using defaults")
        return cls()

    def evaluate(self, context: Dict[str, Any]) -> List[RuleEvaluation]:
        """
        Evaluate all rules against the context, return list of evaluations.
        """
        evaluations: List[RuleEvaluation] = []
        for rule in self._rules:
            triggered, reason = self._evaluate_condition(
                rule.get("condition_expression"), context
            )
            impact = rule["base_weight"] if triggered else 0
            evaluations.append(RuleEvaluation(
                code=rule["code"],
                name=rule["name"],
                triggered=triggered,
                impact=impact,
                blocking=rule.get("is_blocking", False) and triggered,
                severity=rule.get("severity", "MEDIUM"),
                reason=reason,
            ))
        return evaluations

    def _evaluate_condition(
        self, condition_json: Optional[str], context: Dict[str, Any]
    ) -> tuple[bool, str]:
        """
        Evaluate a simple JSON DSL condition:
          {"field": "...", "op": "eq|gt|gte|lt|lte|in|neq", "value": ...}
        """
        if not condition_json:
            return False, "No condition defined"

        try:
            cond = json.loads(condition_json) if isinstance(condition_json, str) else condition_json
        except Exception:
            return False, "Malformed condition JSON"

        field = cond.get("field")
        op = cond.get("op", "eq")
        target = cond.get("value")
        actual = context.get(field)

        if actual is None:
            return False, f"Context missing field: {field}"

        try:
            if op == "eq":
                triggered = actual == target
            elif op == "neq":
                triggered = actual != target
            elif op == "gt":
                triggered = actual > target
            elif op == "gte":
                triggered = actual >= target
            elif op == "lt":
                triggered = actual < target
            elif op == "lte":
                triggered = actual <= target
            elif op == "in":
                triggered = actual in target
            else:
                triggered = False

            reason = f"{field} {op} {target} → {'TRIGGERED' if triggered else 'not triggered'} (actual={actual})"
            return triggered, reason
        except Exception as exc:
            return False, f"Condition evaluation error: {exc}"
