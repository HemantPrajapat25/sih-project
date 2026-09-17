from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.models import DecommissionedNumber, RiskEvaluation, User
from app.schemas.schemas import RiskOverrideRequest, RiskSimulationRequest, RiskSimulationResponse, RiskFactorBreakdown
from app.api.deps import get_current_user, require_permission
from app.core.rbac import Permission
from app.services.risk_engine import calculate_risk
from app.services.audit import record_audit_log

router = APIRouter()

@router.post("/simulate", response_model=RiskSimulationResponse)
async def simulate_risk_evaluation(
    req: RiskSimulationRequest,
    current_user: User = Depends(require_permission(Permission.RISK_READ))
):
    """
    Simulates real-time risk score based on parameters without mutating database state.
    """
    now = datetime.now(timezone.utc)
    decom_date = now - timedelta(days=req.cooling_days_elapsed)
    cooling_end = decom_date + timedelta(days=req.min_cooling_required)

    # Build mock notifications
    class MockProvider:
        def __init__(self, cat):
            self.category = cat

    class MockNotification:
        def __init__(self, cat, status):
            self.provider = MockProvider(cat)
            self.status = status

    mock_notifs = []
    if req.has_banking_service:
        mock_notifs.append(MockNotification("BANKING", "SENT" if req.unacknowledged_providers_count > 0 else "REMEDIATED"))
    if req.has_fintech_service:
        mock_notifs.append(MockNotification("FINTECH", "SENT" if req.unacknowledged_providers_count > 1 else "REMEDIATED"))
    
    score, level, eligibility, factors = calculate_risk(
        decommissioned_at=decom_date,
        cooling_end_date=cooling_end,
        notifications=mock_notifs,
        historical_recycles=req.prior_recycling_count
    )

    return RiskSimulationResponse(
        simulated_score=score,
        simulated_level=level,
        recommended_eligibility=eligibility,
        breakdown=[
            RiskFactorBreakdown(
                name=f["name"],
                weight=f["weight"],
                score_contribution=f["score_contribution"],
                description=f["description"]
            ) for f in factors
        ]
    )

@router.post("/override/{number_id}")
async def override_risk_score(
    number_id: str,
    req: RiskOverrideRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.RISK_OVERRIDE))
):
    res = await db.execute(select(DecommissionedNumber).where(DecommissionedNumber.id == number_id))
    number = res.scalars().first()
    if not number:
        raise HTTPException(status_code=404, detail="Number not found")

    old_score = number.risk_score
    number.risk_score = req.new_risk_score
    
    if req.new_risk_score <= 25:
        number.risk_level = "LOW"
    elif req.new_risk_score <= 55:
        number.risk_level = "MEDIUM"
    elif req.new_risk_score <= 79:
        number.risk_level = "HIGH"
    else:
        number.risk_level = "CRITICAL"

    await db.commit()

    await record_audit_log(
        db=db,
        actor_email=current_user.email,
        actor_role=current_user.role,
        organization_name="Telecom Operator",
        action="RISK_SCORE_OVERRIDDEN",
        entity_type="NUMBER",
        entity_id=number_id,
        details=f"Overrode risk score from {old_score} to {req.new_risk_score}. Reason: {req.reason}"
    )

    return {"message": "Risk score overridden successfully", "new_score": number.risk_score, "new_level": number.risk_level}


@router.post("/assess/{number_id}")
async def run_modular_risk_assessment(
    number_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.RISK_READ))
):
    """
    Runs the modular Phase 3 risk assessment pipeline for a decommissioned number.
    Calculates all 10 privacy-preserving factors, applies DB rules, and returns an explainable report.
    """
    from app.services.risk.assessment import RiskAssessmentService
    from app.services.risk.scorer import DEFAULT_WEIGHTS

    stmt = select(DecommissionedNumber).where(DecommissionedNumber.id == number_id)
    number = (await db.execute(stmt)).scalar_one_or_none()
    if not number:
        raise HTTPException(status_code=404, detail="Number not found")

    svc = RiskAssessmentService(db)
    result = await svc.assess(number=number, triggered_by=current_user.email)

    # Update number risk score
    number.risk_score = result.score
    number.risk_level = result.level
    await db.commit()

    return {
        "number_id": number_id,
        "masked_number": number.masked_number,
        "carrier": number.carrier,
        "score": result.score,
        "level": result.level,
        "recommendation": result.recommendation,
        "is_blocked": result.is_blocked,
        "blocking_rules": result.blocking_rules,
        "summary": result.summary,
        "detail_explanation": result.detail_explanation,
        "factors": [
            {
                "name": f.name,
                "weight": f.weight,
                "normalized_score": f.normalized_score,
                "contribution": f.contribution,
                "explanation": f.explanation,
                "evidence": f.evidence
            }
            for f in result.factors
        ],
        "rules_applied": [
            {
                "code": r.code,
                "name": r.name,
                "triggered": r.triggered,
                "impact": r.impact,
                "is_blocking": r.blocking,
                "evidence": r.reason
            }
            for r in result.rules_applied
        ]
    }


@router.get("/weights")
async def get_risk_factor_weights(
    current_user: User = Depends(require_permission(Permission.RISK_READ))
):
    """
    Returns current active weights for all 10 risk factors.
    """
    from app.services.risk.scorer import DEFAULT_WEIGHTS
    return {
        "weights": DEFAULT_WEIGHTS,
        "total_weight": sum(DEFAULT_WEIGHTS.values())
    }


@router.get("/rules")
async def get_risk_rules(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.RISK_READ))
):
    """
    Returns active risk rules evaluated by the risk engine.
    """
    from app.services.risk.rules import RiskRuleEngine
    engine = await RiskRuleEngine.from_db(db)
    return [
        {
            "code": r.get("code"),
            "name": r.get("name"),
            "base_weight": r.get("base_weight", 0),
            "is_blocking": r.get("is_blocking", False),
            "severity": r.get("severity", "MEDIUM"),
            "condition_expression": r.get("condition_expression")
        }
        for r in engine._rules
    ]
