"""
NumberGuard — System Settings API (Phase 2)
Runtime K/V configuration management for operators.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.models import User
from app.schemas.schemas import SystemSettingOut, SystemSettingUpdate
from app.api.deps import get_current_user, require_permission
from app.core.rbac import Permission
from app.services.settings_service import list_settings, set_setting, get_setting
from app.services.audit import record_audit_log

router = APIRouter()


@router.get("", response_model=List[SystemSettingOut])
async def list_system_settings(
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.ADMIN_SETTINGS)),
):
    """
    List all non-sensitive system settings.
    SUPER_ADMIN can view all categories.
    
    Categories: RISK, COOLING, NOTIFICATIONS, SECURITY, GENERAL
    """
    settings = await list_settings(db, category=category, include_sensitive=False)
    return settings


@router.get("/{key}", response_model=SystemSettingOut)
async def get_system_setting(
    key: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.ADMIN_SETTINGS)),
):
    """Get a specific system setting by key."""
    from sqlalchemy import select
    from app.models.models import SystemSetting
    res = await db.execute(
        select(SystemSetting).where(SystemSetting.key == key)
    )
    setting = res.scalars().first()
    if not setting:
        raise HTTPException(status_code=404, detail=f"Setting '{key}' not found")
    return setting


@router.put("/{key}", response_model=SystemSettingOut)
async def update_system_setting(
    key: str,
    req: SystemSettingUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.ADMIN_SETTINGS)),
):
    """
    Update a system setting value.
    Read-only settings cannot be modified.
    
    Changes take effect immediately and override environment variables.
    """
    try:
        setting = await set_setting(
            db=db,
            key=key,
            value=req.value,
            updated_by=current_user.email,
            description=req.description,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    await record_audit_log(
        db=db,
        actor_email=current_user.email,
        actor_role=current_user.role,
        organization_name="NumberGuard",
        action="SYSTEM_SETTING_UPDATED",
        entity_type="SETTING",
        entity_id=key,
        details=f"Updated setting '{key}' to '{req.value}'",
    )
    return setting
