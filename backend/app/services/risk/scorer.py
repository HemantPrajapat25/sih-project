"""
NumberGuard — Risk Score Calculator (Phase 3)

Aggregates factor scores using configurable database weights.
Produces a final 0–100 score, risk level, and human-readable explanation.

Default weights (override via DB system_settings):
  recycling_factor       = 10
  number_age_factor      = 5
  spam_factor            = 15
  fraud_factor           = 20
  unresolved_factor      = 15
  otp_factor             = 10
  provider_count_factor  = 5
  criticality_factor     = 15
  history_factor         = 3
  override_factor        = 2
  Total max = 100
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .rules import RuleEvaluation


# Default factor max-weights (sum = 100)
DEFAULT_WEIGHTS: Dict[str, int] = {
    "recycling_history":             10,
    "number_age":                     5,
    "spam_reputation":               15,
    "fraud_signals":                 20,
    "unresolved_associations":       15,
    "otp_dependencies":              10,
    "participating_providers_count":  5,
    "provider_criticality":          15,
    "previous_risk_history":          3,
    "manual_override":                2,
}

# Risk level thresholds
RISK_THRESHOLDS = [
    (25,  "LOW"),
    (49,  "MODERATE"),
    (74,  "HIGH"),
    (100, "CRITICAL"),
]

# Allocation recommendation map
RECOMMENDATION_MAP = {
    "LOW":      "APPROVE_REALLOCATION",
    "MODERATE": "APPROVE_WITH_MONITORING",
    "HIGH":     "MANUAL_REVIEW_REQUIRED",
    "CRITICAL": "BLOCK_REALLOCATION",
}


@dataclass
class ScoredFactor:
    name: str
    weight: int            # max points available
    normalized_score: float  # [0, 1] from factor calculator
    contribution: int      # actual points = round(weight * normalized_score)
    explanation: str
    evidence: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RiskScoreResult:
    score: int
    level: str
    recommendation: str
    factors: List[ScoredFactor]
    rules_applied: List[RuleEvaluation]
    is_blocked: bool
    blocking_rules: List[str]
    summary: str
    detail_explanation: str


class RiskScoreCalculator:
    """
    Aggregates normalized factor scores → final 0-100 score.
    Applies rule adjustments (bonuses/penalties + blocking overrides).
    """

    def __init__(self, weights: Optional[Dict[str, int]] = None):
        self.weights = weights or DEFAULT_WEIGHTS

    def calculate(
        self,
        factor_results: Dict[str, tuple],  # factor_name → (norm_score, explanation, evidence)
        rule_evaluations: List[RuleEvaluation],
    ) -> RiskScoreResult:
        """
        factor_results: output from RiskFactorCalculator methods
        rule_evaluations: output from RiskRuleEngine.evaluate()
        """
        # --- Step 1: Score each factor ---
        scored_factors: List[ScoredFactor] = []
        base_score = 0

        for factor_name, weight in self.weights.items():
            if factor_name in factor_results:
                norm_score, explanation, evidence = factor_results[factor_name]
                contribution = round(weight * norm_score)
                base_score += contribution
                scored_factors.append(ScoredFactor(
                    name=factor_name,
                    weight=weight,
                    normalized_score=norm_score,
                    contribution=contribution,
                    explanation=explanation,
                    evidence=evidence,
                ))

        # --- Step 2: Apply rule adjustments ---
        rule_adjustment = 0
        blocking_rules: List[str] = []
        is_blocked = False

        for rule in rule_evaluations:
            if rule.triggered:
                rule_adjustment += rule.impact
                if rule.blocking:
                    is_blocked = True
                    blocking_rules.append(f"{rule.name} ({rule.code})")

        final_score = max(0, min(base_score + rule_adjustment, 100))

        # --- Step 3: Determine level ---
        level = "CRITICAL"
        for threshold, lvl in RISK_THRESHOLDS:
            if final_score <= threshold:
                level = lvl
                break

        # Blocking rules force CRITICAL regardless of score
        if is_blocked:
            level = "CRITICAL"
            final_score = max(final_score, 75)

        recommendation = RECOMMENDATION_MAP.get(level, "MANUAL_REVIEW_REQUIRED")

        # --- Step 4: Generate explanation ---
        triggered_rules = [r for r in rule_evaluations if r.triggered]
        top_factors = sorted(scored_factors, key=lambda f: -f.contribution)[:4]

        factor_lines = [
            f"• {f.explanation} [{f.contribution}/{f.weight} pts]"
            for f in top_factors if f.contribution > 0
        ]
        rule_lines = [f"• Rule triggered: {r.name}" for r in triggered_rules]

        detail = "\n".join(
            [f"Risk Score: {final_score} — Level: {level}", ""]
            + (["Factors:"] + factor_lines if factor_lines else [])
            + (["Rules:"] + rule_lines if rule_lines else [])
            + (["Blocking:"] + [f"  ⛔ {b}" for b in blocking_rules] if blocking_rules else [])
            + [f"\nRecommendation: {recommendation}"]
        )

        summary = self._build_summary(final_score, level, scored_factors, triggered_rules, blocking_rules)

        return RiskScoreResult(
            score=final_score,
            level=level,
            recommendation=recommendation,
            factors=scored_factors,
            rules_applied=rule_evaluations,
            is_blocked=is_blocked,
            blocking_rules=blocking_rules,
            summary=summary,
            detail_explanation=detail,
        )

    def _build_summary(
        self,
        score: int,
        level: str,
        factors: List[ScoredFactor],
        triggered_rules: List[RuleEvaluation],
        blocking_rules: List[str],
    ) -> str:
        parts = []
        if blocking_rules:
            parts.append(f"{len(blocking_rules)} blocking rule(s) active")
        high_factors = [f for f in factors if f.contribution > 10]
        if high_factors:
            parts.append(", ".join(f.name.replace("_", " ") for f in high_factors[:3]))
        if not parts:
            parts.append("low overall risk profile")
        return f"Score {score} ({level}): " + "; ".join(parts)
