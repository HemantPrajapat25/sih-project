"""
NumberGuard — Risk Factor Calculator (Phase 3)

10 independent, privacy-preserving factor functions.
Each returns:
  (raw_score: float, explanation: str, evidence: dict)

raw_score is in [0, 1] — normalized to factor max_weight by the scorer.
No raw phone numbers are ever accessed.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

# Type alias for a factor result
FactorResult = Tuple[float, str, Dict[str, Any]]


class RiskFactorCalculator:
    """
    Calculates individual risk factor scores from metadata/signals only.
    All methods are pure functions — no DB access, fully unit-testable.
    """

    # -----------------------------------------------------------------------
    # Factor 1: Recycling History
    # -----------------------------------------------------------------------
    @staticmethod
    def recycling_history(total_recycling_count: int) -> FactorResult:
        """
        Higher recycling velocity = higher risk of stale digital associations.
        0 recycles → 0.0, 1 → 0.3, 2 → 0.6, 3+ → 1.0
        """
        if total_recycling_count == 0:
            score = 0.0
            explanation = "No prior recycling history — clean first assignment"
        elif total_recycling_count == 1:
            score = 0.30
            explanation = "Previously recycled once — moderate association risk"
        elif total_recycling_count == 2:
            score = 0.60
            explanation = "Recycled twice — elevated stale-association probability"
        else:
            score = 1.0
            explanation = f"High recycling velocity ({total_recycling_count} cycles) — critical historical risk"

        return score, explanation, {"recycling_count": total_recycling_count}

    # -----------------------------------------------------------------------
    # Factor 2: Number Age / History
    # -----------------------------------------------------------------------
    @staticmethod
    def number_age(first_seen_at: datetime, decommissioned_at: datetime) -> FactorResult:
        """
        Older numbers have accumulated more digital associations.
        < 6 months → 0.0, 6-12m → 0.25, 1-3yr → 0.5, 3-7yr → 0.75, 7yr+ → 1.0
        """
        if first_seen_at.tzinfo is None:
            first_seen_at = first_seen_at.replace(tzinfo=timezone.utc)
        if decommissioned_at.tzinfo is None:
            decommissioned_at = decommissioned_at.replace(tzinfo=timezone.utc)

        age_days = max((decommissioned_at - first_seen_at).days, 0)
        age_months = age_days / 30.44

        if age_months < 6:
            score = 0.0
            label = f"{age_days} days — very new"
        elif age_months < 12:
            score = 0.25
            label = f"{int(age_months)} months — moderate age"
        elif age_months < 36:
            score = 0.50
            label = f"{int(age_months // 12)}y {int(age_months % 12)}m — established"
        elif age_months < 84:
            score = 0.75
            label = f"{int(age_months // 12)} years — long-lived, high association risk"
        else:
            score = 1.0
            label = f"{int(age_months // 12)}+ years — very long-lived, critical risk"

        explanation = f"Number age: {label}"
        return score, explanation, {"age_days": age_days, "age_months": round(age_months, 1)}

    # -----------------------------------------------------------------------
    # Factor 3: Spam Reputation
    # -----------------------------------------------------------------------
    @staticmethod
    def spam_reputation(spam_signal: str) -> FactorResult:
        """
        External spam/nuisance signal from phone intelligence adapter.
        Values: NONE, LOW, MEDIUM, HIGH, CRITICAL
        """
        mapping = {
            "NONE":     (0.0,  "No spam signals detected"),
            "LOW":      (0.20, "Minor spam activity reported by intelligence feed"),
            "MEDIUM":   (0.50, "Moderate spam reputation — requires monitoring"),
            "HIGH":     (0.80, "High spam reputation — significant reuse risk"),
            "CRITICAL": (1.0,  "Critical spam/abuse reputation — block reallocation"),
        }
        normalized = spam_signal.upper() if spam_signal else "NONE"
        score, explanation = mapping.get(normalized, (0.30, f"Unknown spam signal: {spam_signal}"))
        return score, explanation, {"spam_signal": normalized}

    # -----------------------------------------------------------------------
    # Factor 4: Fraud Signals
    # -----------------------------------------------------------------------
    @staticmethod
    def fraud_signals(fraud_signal: str, fraud_incident_count: int = 0) -> FactorResult:
        """
        Fraud signal from intelligence adapter plus incident history.
        """
        base_mapping = {
            "NONE":     0.0,
            "LOW":      0.25,
            "MEDIUM":   0.50,
            "HIGH":     0.80,
            "CRITICAL": 1.0,
        }
        normalized = fraud_signal.upper() if fraud_signal else "NONE"
        base_score = base_mapping.get(normalized, 0.30)

        # Add incremental penalty for known incidents (capped)
        incident_penalty = min(fraud_incident_count * 0.10, 0.20)
        score = min(base_score + incident_penalty, 1.0)

        if fraud_incident_count > 0:
            explanation = f"Fraud signal: {normalized} + {fraud_incident_count} reported incident(s)"
        else:
            explanation = f"Fraud signal: {normalized}"

        return score, explanation, {
            "fraud_signal": normalized,
            "incident_count": fraud_incident_count,
        }

    # -----------------------------------------------------------------------
    # Factor 5: Unresolved Provider Associations
    # -----------------------------------------------------------------------
    @staticmethod
    def unresolved_associations(
        active_association_count: int,
        total_association_count: int,
    ) -> FactorResult:
        """
        Ratio of ACTIVE (unresolved) to total associations.
        0 unresolved → 0.0, all unresolved → 1.0
        """
        if total_association_count == 0:
            return 0.0, "No known provider associations on record", {
                "active": 0, "total": 0
            }

        ratio = active_association_count / max(total_association_count, 1)
        # Also penalize raw count
        count_score = min(active_association_count / 10.0, 1.0)
        score = (ratio * 0.6) + (count_score * 0.4)
        score = min(score, 1.0)

        if active_association_count == 0:
            explanation = f"All {total_association_count} provider associations resolved"
        else:
            explanation = (
                f"{active_association_count}/{total_association_count} associations still ACTIVE — "
                f"remediation incomplete"
            )

        return score, explanation, {
            "active_associations": active_association_count,
            "total_associations": total_association_count,
            "unresolved_ratio": round(ratio, 2),
        }

    # -----------------------------------------------------------------------
    # Factor 6: OTP / Recovery Dependencies
    # -----------------------------------------------------------------------
    @staticmethod
    def otp_dependencies(
        otp_service_count: int,
        recovery_service_count: int,
    ) -> FactorResult:
        """
        Numbers used as OTP targets or account recovery contacts carry extra risk.
        Financial OTPs are particularly sensitive.
        """
        total = otp_service_count + recovery_service_count
        if total == 0:
            return 0.0, "No OTP or account recovery dependencies detected", {
                "otp_services": 0, "recovery_services": 0
            }

        # OTP dependencies are more critical than generic recovery
        score = min((otp_service_count * 0.30 + recovery_service_count * 0.20), 1.0)
        parts = []
        if otp_service_count > 0:
            parts.append(f"{otp_service_count} OTP service(s)")
        if recovery_service_count > 0:
            parts.append(f"{recovery_service_count} account recovery link(s)")

        explanation = f"Pending unlinked: {', '.join(parts)}"

        return score, explanation, {
            "otp_services": otp_service_count,
            "recovery_services": recovery_service_count,
        }

    # -----------------------------------------------------------------------
    # Factor 7: Participating Provider Count
    # -----------------------------------------------------------------------
    @staticmethod
    def participating_providers_count(
        notified_provider_count: int,
        unacknowledged_count: int,
    ) -> FactorResult:
        """
        More providers = higher surface area. Unacknowledged = unresolved risk.
        """
        if notified_provider_count == 0:
            return 0.0, "No providers notified — number not in active use", {
                "notified": 0, "unacknowledged": 0
            }

        # Unack ratio drives score
        unack_ratio = unacknowledged_count / max(notified_provider_count, 1)
        score = min((unack_ratio * 0.7) + (min(notified_provider_count, 10) / 10 * 0.3), 1.0)

        if unacknowledged_count == 0:
            explanation = f"All {notified_provider_count} notified provider(s) acknowledged"
        else:
            explanation = (
                f"{unacknowledged_count}/{notified_provider_count} provider(s) have NOT "
                f"acknowledged the decommission event"
            )

        return score, explanation, {
            "notified": notified_provider_count,
            "unacknowledged": unacknowledged_count,
            "ack_ratio": round(1 - unack_ratio, 2),
        }

    # -----------------------------------------------------------------------
    # Factor 8: Provider Criticality
    # -----------------------------------------------------------------------
    @staticmethod
    def provider_criticality(
        provider_categories: List[str],  # e.g. ["BANKING", "FINTECH", "ECOMMERCE"]
        unresolved_categories: List[str],
    ) -> FactorResult:
        """
        Critical categories (BANKING, FINTECH) carry much higher weight.
        """
        CRITICALITY_WEIGHTS = {
            "BANKING":   1.0,
            "FINTECH":   0.85,
            "IDENTITY":  0.80,
            "TELECOM":   0.70,
            "ECOMMERCE": 0.50,
            "SOCIAL":    0.35,
            "GENERAL":   0.20,
            "OTHER":     0.15,
        }

        if not unresolved_categories:
            return 0.0, "No unresolved critical-category provider associations", {
                "all_categories": provider_categories,
                "unresolved_categories": [],
            }

        # Max criticality score of unresolved providers
        max_crit = max(
            (CRITICALITY_WEIGHTS.get(cat.upper(), 0.15) for cat in unresolved_categories),
            default=0.0,
        )
        # Weighted average for cumulative effect
        avg_crit = sum(
            CRITICALITY_WEIGHTS.get(cat.upper(), 0.15) for cat in unresolved_categories
        ) / max(len(unresolved_categories), 1)

        score = min((max_crit * 0.6) + (avg_crit * 0.4), 1.0)

        critical = [c for c in unresolved_categories if c.upper() in ("BANKING", "FINTECH", "IDENTITY")]
        explanation = (
            f"Unresolved high-criticality providers: {', '.join(unresolved_categories)}"
            + (f" ({len(critical)} critical-tier)" if critical else "")
        )

        return score, explanation, {
            "unresolved_categories": unresolved_categories,
            "critical_tier_count": len(critical),
            "max_criticality_score": round(max_crit, 2),
        }

    # -----------------------------------------------------------------------
    # Factor 9: Previous Risk History
    # -----------------------------------------------------------------------
    @staticmethod
    def previous_risk_history(
        prior_assessment_scores: List[int],
        prior_level_counts: Optional[Dict[str, int]] = None,
    ) -> FactorResult:
        """
        Consistently high historical scores indicate a persistently risky number.
        """
        if not prior_assessment_scores:
            return 0.0, "No prior risk assessments on record", {
                "assessment_count": 0
            }

        avg_score = sum(prior_assessment_scores) / len(prior_assessment_scores)
        recent_scores = prior_assessment_scores[-3:]  # weight recency
        recent_avg = sum(recent_scores) / len(recent_scores)

        # Normalize to [0, 1]
        score = min((recent_avg * 0.7 + avg_score * 0.3) / 100, 1.0)

        explanation = (
            f"Historical avg risk: {avg_score:.0f} "
            f"(recent {len(recent_scores)} assessments avg: {recent_avg:.0f})"
        )

        return score, explanation, {
            "assessment_count": len(prior_assessment_scores),
            "historical_avg": round(avg_score, 1),
            "recent_avg": round(recent_avg, 1),
        }

    # -----------------------------------------------------------------------
    # Factor 10: Manual Override
    # -----------------------------------------------------------------------
    @staticmethod
    def manual_override(
        override_active: bool,
        override_score: Optional[int] = None,
        override_reason: Optional[str] = None,
    ) -> FactorResult:
        """
        An active manual override sets or adjusts the score.
        This factor returns the normalized override value directly.
        """
        if not override_active or override_score is None:
            return 0.0, "No manual risk override active", {"override_active": False}

        score = min(override_score / 100.0, 1.0)
        explanation = (
            f"MANUAL OVERRIDE active: score set to {override_score}"
            + (f" — Reason: {override_reason}" if override_reason else "")
        )
        return score, explanation, {
            "override_active": True,
            "override_score": override_score,
            "override_reason": override_reason,
        }
