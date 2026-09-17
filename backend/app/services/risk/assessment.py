"""
NumberGuard — Risk Assessment Service (Phase 3)

Orchestrates the full risk assessment pipeline:
  1. Fetch number metadata + signals from DB
  2. Call RiskFactorCalculator for each of 10 factors
  3. Build rule context dict
  4. Load rules via RiskRuleEngine
  5. Aggregate with RiskScoreCalculator
  6. Persist to risk_evaluations table
  7. Return fully explainable RiskScoreResult

Operates on signals/metadata ONLY — no raw phone numbers accessed.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.models.models import (
    DecommissionedNumber,
    MobileNumber,
    ProviderNotification,
    ProviderNumberAssociation,
    RiskEvaluation,
    ServiceProvider,
    SystemSetting,
)
from app.services.risk.factors import RiskFactorCalculator
from app.services.risk.rules import RiskRuleEngine
from app.services.risk.scorer import RiskScoreCalculator, DEFAULT_WEIGHTS, RiskScoreResult

logger = logging.getLogger("numberguard.risk.assessment")


class RiskAssessmentService:
    """
    Full assessment pipeline for a DecommissionedNumber.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.calc = RiskFactorCalculator()

    async def assess(
        self,
        number: DecommissionedNumber,
        triggered_by: str = "SYSTEM",
        phone_intel_signals: Optional[Dict[str, Any]] = None,
    ) -> RiskScoreResult:
        """
        Run full risk assessment and persist the result.
        phone_intel_signals: {"spam": "HIGH", "fraud": "NONE", "fraud_incidents": 0}
        """
        signals = phone_intel_signals or {}
        now = datetime.now(timezone.utc)

        # Ensure TZ-aware dates
        decom_at = number.decommissioned_at
        cooling_end = number.cooling_end_date
        if decom_at.tzinfo is None:
            decom_at = decom_at.replace(tzinfo=timezone.utc)
        if cooling_end.tzinfo is None:
            cooling_end = cooling_end.replace(tzinfo=timezone.utc)

        cooling_completed = now >= cooling_end

        # --- Fetch provider notifications ---
        notif_res = await self.db.execute(
            select(ProviderNotification)
            .options(selectinload(ProviderNotification.provider))
            .where(ProviderNotification.number_id == number.id)
        )
        notifications = notif_res.scalars().all()

        total_notified = len(notifications)
        unacknowledged = sum(
            1 for n in notifications
            if n.status not in ("ACKNOWLEDGED", "REMEDIATED", "NOT_APPLICABLE")
        )
        all_acked = (total_notified > 0 and unacknowledged == 0)

        # Provider categories
        all_categories = [
            n.provider.category for n in notifications if n.provider
        ]
        unresolved_categories = [
            n.provider.category for n in notifications
            if n.provider and n.status not in ("REMEDIATED", "NOT_APPLICABLE", "ACKNOWLEDGED")
        ]
        critical_unresolved = sum(
            1 for cat in unresolved_categories
            if cat.upper() in ("BANKING", "FINTECH", "IDENTITY")
        )

        # OTP/Recovery detection by service type (from provider_number_associations)
        otp_services = 0
        recovery_services = 0
        # Note: In a real deployment this would query provider_number_associations
        # For now we infer from provider category if notification is unresolved
        for n in notifications:
            if n.provider and n.status not in ("REMEDIATED", "NOT_APPLICABLE"):
                cat = (n.provider.category or "").upper()
                if cat in ("BANKING", "FINTECH", "IDENTITY"):
                    otp_services += 1  # High-risk categories likely have OTP
                elif cat == "ECOMMERCE":
                    recovery_services += 1

        # --- Fetch MobileNumber for recycling + age ---
        mobile_num: Optional[MobileNumber] = None
        recycling_count = 0
        first_seen_at = decom_at  # fallback

        mn_res = await self.db.execute(
            select(MobileNumber).where(MobileNumber.phone_hash == number.phone_hash)
        )
        mobile_num = mn_res.scalars().first()
        if mobile_num:
            recycling_count = mobile_num.total_recycling_count or 0
            first_seen_at = mobile_num.first_seen_at or decom_at

        # --- Fetch prior assessment scores ---
        prior_res = await self.db.execute(
            select(RiskEvaluation.score)
            .where(RiskEvaluation.number_id == number.id)
            .order_by(RiskEvaluation.evaluated_at.desc())
            .limit(10)
        )
        prior_scores = [row[0] for row in prior_res.fetchall()]

        # --- Load configurable weights from DB settings ---
        weights = await self._load_weights()

        # --- Calculate all 10 factors ---
        spam_signal = signals.get("spam", "NONE")
        fraud_signal = signals.get("fraud", "NONE")
        fraud_incidents = signals.get("fraud_incidents", 0)
        override_active = signals.get("override_active", False)
        override_score = signals.get("override_score", None)
        override_reason = signals.get("override_reason", None)

        factor_results = {
            "recycling_history": RiskFactorCalculator.recycling_history(recycling_count),
            "number_age": RiskFactorCalculator.number_age(first_seen_at, decom_at),
            "spam_reputation": RiskFactorCalculator.spam_reputation(spam_signal),
            "fraud_signals": RiskFactorCalculator.fraud_signals(fraud_signal, fraud_incidents),
            "unresolved_associations": RiskFactorCalculator.unresolved_associations(
                len(unresolved_categories), total_notified
            ),
            "otp_dependencies": RiskFactorCalculator.otp_dependencies(otp_services, recovery_services),
            "participating_providers_count": RiskFactorCalculator.participating_providers_count(
                total_notified, unacknowledged
            ),
            "provider_criticality": RiskFactorCalculator.provider_criticality(
                all_categories, unresolved_categories
            ),
            "previous_risk_history": RiskFactorCalculator.previous_risk_history(prior_scores),
            "manual_override": RiskFactorCalculator.manual_override(
                override_active, override_score, override_reason
            ),
        }

        # --- Build rule context ---
        rule_context = {
            "cooling_completed": cooling_completed,
            "unresolved_critical_providers": critical_unresolved,
            "fraud_signal": fraud_signal.upper(),
            "spam_signal": spam_signal.upper(),
            "all_providers_acknowledged": all_acked,
            "recycling_count": recycling_count,
            "otp_services_unlinked": (otp_services == 0),
            "manual_override_active": override_active,
            "risk_score_before_rules": 0,  # will be approximate
        }

        # --- Load and evaluate rules ---
        rule_engine = await RiskRuleEngine.from_db(self.db)
        rule_evaluations = rule_engine.evaluate(rule_context)

        # --- Calculate final score ---
        scorer = RiskScoreCalculator(weights)
        result = scorer.calculate(factor_results, rule_evaluations)

        # --- Persist to DB ---
        await self._persist(number.id, result, triggered_by)

        # --- Update number record ---
        number.risk_score = result.score
        number.risk_level = result.level
        if result.is_blocked:
            number.allocation_eligibility = "BLOCKED"
        elif not cooling_completed:
            number.allocation_eligibility = "COOLING_HOLD"
        elif result.level in ("HIGH", "CRITICAL"):
            number.allocation_eligibility = "MANUAL_REVIEW_REQUIRED"
        else:
            number.allocation_eligibility = "ELIGIBLE"
        number.updated_at = now
        await self.db.commit()

        logger.info(
            f"Risk assessed number={number.id[:8]} "
            f"score={result.score} level={result.level} "
            f"blocked={result.is_blocked}"
        )
        return result

    async def _load_weights(self) -> Dict[str, int]:
        """Load configurable factor weights from system_settings table."""
        WEIGHT_KEY_MAP = {
            "risk.weight.recycling": "recycling_history",
            "risk.weight.age": "number_age",
            "risk.weight.spam": "spam_reputation",
            "risk.weight.fraud": "fraud_signals",
            "risk.weight.unresolved": "unresolved_associations",
            "risk.weight.otp": "otp_dependencies",
            "risk.weight.providers": "participating_providers_count",
            "risk.weight.criticality": "provider_criticality",
            "risk.weight.history": "previous_risk_history",
            "risk.weight.override": "manual_override",
        }
        weights = dict(DEFAULT_WEIGHTS)  # start with defaults
        try:
            res = await self.db.execute(
                select(SystemSetting).where(
                    SystemSetting.key.in_(list(WEIGHT_KEY_MAP.keys()))
                )
            )
            for setting in res.scalars().all():
                factor_name = WEIGHT_KEY_MAP.get(setting.key)
                if factor_name:
                    weights[factor_name] = int(setting.value)
        except Exception as exc:
            logger.warning(f"Could not load weights from DB: {exc}")
        return weights

    async def _persist(
        self, number_id: str, result: RiskScoreResult, evaluated_by: str
    ) -> None:
        """Persist the risk assessment result to risk_evaluations."""
        try:
            factors_json = json.dumps([
                {
                    "name": f.name,
                    "weight": f.weight,
                    "contribution": f.contribution,
                    "explanation": f.explanation,
                    "evidence": f.evidence,
                }
                for f in result.factors
            ])
            rules_json = json.dumps([
                {
                    "code": r.code,
                    "name": r.name,
                    "triggered": r.triggered,
                    "impact": r.impact,
                    "blocking": r.blocking,
                }
                for r in result.rules_applied
            ])
            evaluation = RiskEvaluation(
                number_id=number_id,
                score=result.score,
                risk_level=result.level,
                factor_banking_weight=next(
                    (f.contribution for f in result.factors if f.name == "provider_criticality"), 0
                ),
                factor_cooling_weight=0,  # cooling is now a rule, not a separate factor
                factor_sla_weight=next(
                    (f.contribution for f in result.factors if f.name == "unresolved_associations"), 0
                ),
                factor_velocity_weight=next(
                    (f.contribution for f in result.factors if f.name == "recycling_history"), 0
                ),
                details_json=json.dumps({
                    "factors": json.loads(factors_json),
                    "rules": json.loads(rules_json),
                    "recommendation": result.recommendation,
                    "summary": result.summary,
                    "blocking_rules": result.blocking_rules,
                }),
                evaluated_by=evaluated_by,
            )
            self.db.add(evaluation)
            await self.db.flush()
        except Exception as exc:
            logger.error(f"Failed to persist risk evaluation: {exc}")
