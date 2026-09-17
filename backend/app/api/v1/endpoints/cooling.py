from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.models import CoolingRule, User
from app.schemas.schemas import CoolingRuleOut, CoolingRuleCreate, CoolingRuleUpdate
from app.api.deps import get_current_user, require_permission
from app.core.rbac import Permission
from app.services.audit import record_audit_log

router = APIRouter()

@router.get("", response_model=List[CoolingRuleOut])
async def list_cooling_rules(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.NUMBERS_READ))
):
    res = await db.execute(select(CoolingRule).order_by(CoolingRule.created_at))
    rules = res.scalars().all()
    return rules

@router.post("", response_model=CoolingRuleOut)
async def create_cooling_rule(
    req: CoolingRuleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.SETTINGS_MANAGE))
):
    rule = CoolingRule(
        name=req.name,
        carrier=req.carrier,
        category=req.category,
        min_cooling_days=req.min_cooling_days,
        risk_extension_days=req.risk_extension_days,
        auto_extend_on_overdue=req.auto_extend_on_overdue,
        release_condition=req.release_condition or "Zero alerts and cooling elapsed"
    )
    db.add(rule)
    await db.commit()
    await db.refresh(rule)

    await record_audit_log(
        db=db,
        actor_email=current_user.email,
        actor_role=current_user.role,
        organization_name="Telecom Admin",
        action="COOLING_RULE_CREATED",
        entity_type="COOLING_RULE",
        entity_id=rule.id,
        details=f"Configured {rule.name}: {rule.min_cooling_days} min days for {rule.carrier}"
    )

    return rule

@router.patch("/{id}", response_model=CoolingRuleOut)
async def update_cooling_rule(
    id: str,
    req: CoolingRuleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.SETTINGS_MANAGE))
):
    res = await db.execute(select(CoolingRule).where(CoolingRule.id == id))
    rule = res.scalars().first()
    if not rule:
        raise HTTPException(status_code=404, detail="Cooling rule not found")

    if req.name:
        rule.name = req.name
    if req.min_cooling_days is not None:
        rule.min_cooling_days = req.min_cooling_days
    if req.risk_extension_days is not None:
        rule.risk_extension_days = req.risk_extension_days
    if req.auto_extend_on_overdue is not None:
        rule.auto_extend_on_overdue = req.auto_extend_on_overdue
    if req.is_active is not None:
        rule.is_active = req.is_active
    if req.release_condition is not None:
        rule.release_condition = req.release_condition

    await db.commit()
    await db.refresh(rule)

    return rule
