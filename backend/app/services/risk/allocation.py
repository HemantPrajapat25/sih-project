"""
NumberGuard — Allocation Decision Service (Phase 3)

Wraps RiskAssessmentService to produce final allocation decisions
(APPROVED / BLOCKED / DEFERRED / MANUAL_OVERRIDE) with full audit trail.
"""
from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.models import (
    AllocationDecision,
    DecommissionedNumber,
    MobileNumber,
    ProviderNotification,
)
from app.services.risk.assessment import RiskAssessmentService
from app.services.risk.scorer import RiskScoreResult

logger = logging.getLogger("numberguard.risk.allocation")


class AllocationDecisionService:
    """
    Creates final allocation decisions backed by a fresh risk assessment.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def decide(
        self,
        number: DecommissionedNumber,
        decided_by: str,
        decided_by_role: str,
        decision_notes: Optional[str] = None,
        override_justification: Optional[str] = None,
        phone_intel_signals: Optional[Dict[str, Any]] = None,
        force_decision: Optional[str] = None,  # APPROVED / BLOCKED / DEFERRED
    ) -> AllocationDecision:
        """
        Run fresh risk assessment, then create an AllocationDecision record.
        If force_decision is provided, it overrides the computed recommendation.
        """
        now = datetime.now(timezone.utc)

        # --- Run fresh assessment ---
        assessment_svc = RiskAssessmentService(self.db)
        result: RiskScoreResult = await assessment_svc.assess(
            number=number,
            triggered_by=decided_by,
            phone_intel_signals=phone_intel_signals,
        )

        # --- Map recommendation to decision ---
        if force_decision:
            decision = force_decision.upper()
        else:
            recommendation_map = {
                "APPROVE_REALLOCATION":    "APPROVED",
                "APPROVE_WITH_MONITORING": "APPROVED",
                "MANUAL_REVIEW_REQUIRED":  "DEFERRED",
                "BLOCK_REALLOCATION":      "BLOCKED",
            }
            decision = recommendation_map.get(result.recommendation, "DEFERRED")

        # --- Check provider clearance ---
        notif_res = await self.db.execute(
            select(ProviderNotification).where(ProviderNotification.number_id == number.id)
        )
        notifications = notif_res.scalars().all()
        total = len(notifications)
        resolved = sum(
            1 for n in notifications
            if n.status in ("REMEDIATED", "ACKNOWLEDGED", "NOT_APPLICABLE")
        )
        all_cleared = (total == 0 or resolved == total)
        banking_cleared = all(
            n.status in ("REMEDIATED", "ACKNOWLEDGED", "NOT_APPLICABLE")
            for n in notifications
            if n.provider and n.provider.category.upper() in ("BANKING", "FINTECH")
        )

        # --- Check cooling ---
        cooling_end = number.cooling_end_date
        if cooling_end.tzinfo is None:
            cooling_end = cooling_end.replace(tzinfo=timezone.utc)
        cooling_completed = now >= cooling_end

        # --- Create decision record ---
        dec_number = f"DEC-{uuid.uuid4().hex[:8].upper()}"
        allocation = AllocationDecision(
            decision_number=dec_number,
            mobile_number_id=None,  # MobileNumber FK (set if available)
            decision=decision,
            risk_score_at_decision=result.score,
            risk_level_at_decision=result.level,
            cooling_completed=cooling_completed,
            banking_cleared=banking_cleared,
            all_providers_cleared=all_cleared,
            decided_by=decided_by,
            decided_by_role=decided_by_role,
            decision_notes=decision_notes,
            override_justification=override_justification,
            decided_at=now,
        )

        # Try to resolve MobileNumber FK
        mn_res = await self.db.execute(
            select(MobileNumber).where(MobileNumber.phone_hash == number.phone_hash)
        )
        mobile_num = mn_res.scalars().first()
        if mobile_num:
            allocation.mobile_number_id = mobile_num.id

        self.db.add(allocation)
        await self.db.commit()
        await self.db.refresh(allocation)

        logger.info(
            f"AllocationDecision created: {dec_number} "
            f"decision={decision} score={result.score} "
            f"by={decided_by}"
        )
        return allocation

    async def get_decision_context(
        self, number: DecommissionedNumber
    ) -> Dict[str, Any]:
        """
        Quick-read current risk context for a number without creating a decision.
        Used for pre-flight checks in the UI.
        """
        now = datetime.now(timezone.utc)
        cooling_end = number.cooling_end_date
        if cooling_end.tzinfo is None:
            cooling_end = cooling_end.replace(tzinfo=timezone.utc)

        notif_res = await self.db.execute(
            select(ProviderNotification).where(ProviderNotification.number_id == number.id)
        )
        notifications = notif_res.scalars().all()
        total = len(notifications)
        resolved = sum(
            1 for n in notifications
            if n.status in ("REMEDIATED", "ACKNOWLEDGED", "NOT_APPLICABLE")
        )

        return {
            "number_id": number.id,
            "current_risk_score": number.risk_score,
            "current_risk_level": number.risk_level,
            "allocation_eligibility": number.allocation_eligibility,
            "cooling_completed": now >= cooling_end,
            "cooling_days_remaining": max((cooling_end - now).days, 0),
            "total_providers": total,
            "resolved_providers": resolved,
            "unresolved_providers": total - resolved,
            "all_providers_cleared": (total == 0 or resolved == total),
        }
