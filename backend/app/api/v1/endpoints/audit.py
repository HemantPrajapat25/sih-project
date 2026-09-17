from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.db.session import get_db
from app.models.models import AuditLog, User
from app.schemas.schemas import AuditLogOut
from app.api.deps import get_current_user, require_permission
from app.core.rbac import Permission

router = APIRouter()

@router.get("", response_model=List[AuditLogOut])
async def list_audit_logs(
    search: Optional[str] = None,
    action: Optional[str] = None,
    entity_type: Optional[str] = None,
    correlation_id: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.AUDIT_READ))
):
    query = select(AuditLog).order_by(desc(AuditLog.timestamp))

    if search:
        query = query.where(
            (AuditLog.actor_email.ilike(f"%{search}%")) |
            (AuditLog.action.ilike(f"%{search}%")) |
            (AuditLog.details.ilike(f"%{search}%"))
        )
    if action and action != "ALL":
        query = query.where(AuditLog.action == action)
    if entity_type and entity_type != "ALL":
        query = query.where(AuditLog.entity_type == entity_type)
    if correlation_id:
        query = query.where(AuditLog.correlation_id == correlation_id)

    query = query.offset(skip).limit(limit)
    res = await db.execute(query)
    logs = res.scalars().all()
    return logs
