"""
NumberGuard — System Settings Service (Phase 2)
Runtime K/V configuration store with typed value access.
"""
from datetime import datetime, timezone
from typing import Optional, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.models import SystemSetting


def _cast_value(raw: str, value_type: str) -> Any:
    """Cast stored string value to correct Python type."""
    if value_type == "int":
        return int(raw)
    elif value_type == "float":
        return float(raw)
    elif value_type == "bool":
        return raw.lower() in ("true", "1", "yes")
    elif value_type == "json":
        import json
        return json.loads(raw)
    return raw  # string


async def get_setting(db: AsyncSession, key: str, default: Any = None) -> Any:
    """Fetches a setting value by key, returns typed Python value."""
    res = await db.execute(select(SystemSetting).where(SystemSetting.key == key))
    setting = res.scalars().first()
    if not setting:
        return default
    return _cast_value(setting.value, setting.value_type)


async def set_setting(
    db: AsyncSession,
    key: str,
    value: str,
    updated_by: str,
    description: Optional[str] = None,
) -> SystemSetting:
    """Creates or updates a setting."""
    res = await db.execute(select(SystemSetting).where(SystemSetting.key == key))
    setting = res.scalars().first()

    if setting:
        if setting.is_readonly:
            raise ValueError(f"Setting '{key}' is read-only and cannot be modified")
        setting.value = value
        setting.updated_by = updated_by
        setting.updated_at = datetime.now(timezone.utc)
        if description:
            setting.description = description
    else:
        setting = SystemSetting(
            key=key,
            value=value,
            updated_by=updated_by,
            description=description,
            created_at=datetime.now(timezone.utc),
        )
        db.add(setting)

    await db.commit()
    await db.refresh(setting)
    return setting


async def list_settings(
    db: AsyncSession,
    category: Optional[str] = None,
    include_sensitive: bool = False,
) -> List[SystemSetting]:
    """Lists all system settings."""
    query = select(SystemSetting).order_by(SystemSetting.category, SystemSetting.key)
    if category:
        query = query.where(SystemSetting.category == category)
    if not include_sensitive:
        query = query.where(SystemSetting.is_sensitive == False)
    result = await db.execute(query)
    return result.scalars().all()


DEFAULT_SETTINGS = [
    {"key": "risk.threshold.low", "value": "25", "value_type": "int", "category": "RISK",
     "description": "Risk score below which a number is classified LOW", "is_readonly": False},
    {"key": "risk.threshold.medium", "value": "55", "value_type": "int", "category": "RISK",
     "description": "Risk score below which a number is classified MEDIUM", "is_readonly": False},
    {"key": "risk.threshold.high", "value": "79", "value_type": "int", "category": "RISK",
     "description": "Risk score below which a number is classified HIGH", "is_readonly": False},
    {"key": "cooling.default_days.standard", "value": "60", "value_type": "int", "category": "COOLING",
     "description": "Default cooling period for standard decommissions", "is_readonly": False},
    {"key": "cooling.default_days.banking", "value": "90", "value_type": "int", "category": "COOLING",
     "description": "Extended cooling period when banking services are linked", "is_readonly": False},
    {"key": "cooling.default_days.high_risk", "value": "120", "value_type": "int", "category": "COOLING",
     "description": "Maximum cooling for high-risk or disputed numbers", "is_readonly": False},
    {"key": "notifications.max_retries", "value": "3", "value_type": "int", "category": "NOTIFICATIONS",
     "description": "Maximum delivery retry attempts per provider notification", "is_readonly": False},
    {"key": "notifications.retry_backoff_minutes", "value": "60", "value_type": "int", "category": "NOTIFICATIONS",
     "description": "Minutes between retry attempts (base, exponential backoff applied)", "is_readonly": False},
    {"key": "security.phone_pepper_rotation_days", "value": "365", "value_type": "int", "category": "SECURITY",
     "description": "Days between HMAC phone hash pepper rotation", "is_readonly": True},
    {"key": "system.platform_version", "value": "2.0.0", "value_type": "string", "category": "GENERAL",
     "description": "NumberGuard platform version", "is_readonly": True},
    {"key": "system.mock_mode", "value": "true", "value_type": "bool", "category": "GENERAL",
     "description": "Enable mock/sandbox mode for external integrations", "is_readonly": False},
    {"key": "allocation.require_manual_approval_above_risk", "value": "79", "value_type": "int", "category": "RISK",
     "description": "Risk score above which allocation requires manual approval", "is_readonly": False},
]
