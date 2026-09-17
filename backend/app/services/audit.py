import uuid
from typing import Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.models import AuditLog

async def record_audit_log(
    db: AsyncSession,
    actor_email: str,
    actor_role: str,
    organization_name: str,
    action: str,
    entity_type: str,
    entity_id: str,
    correlation_id: Optional[str] = None,
    ip_address: str = "127.0.0.1",
    result: str = "SUCCESS",
    details: Optional[str] = None
) -> AuditLog:
    """
    Creates an immutable audit log entry for every state transition and administrative action.
    """
    if not correlation_id:
        correlation_id = f"CORR-{uuid.uuid4().hex[:12].upper()}"

    log_entry = AuditLog(
        actor_email=actor_email,
        actor_role=actor_role,
        organization_name=organization_name,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        correlation_id=correlation_id,
        ip_address=ip_address,
        result=result,
        details=details
    )
    db.add(log_entry)
    await db.commit()
    await db.refresh(log_entry)
    return log_entry
