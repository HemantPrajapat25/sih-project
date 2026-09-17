from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.db.session import get_db
from app.models.models import ServiceProvider, User
from app.schemas.schemas import ServiceProviderOut, ServiceProviderCreate, ServiceProviderUpdate
from app.api.deps import get_current_user, require_permission
from app.core.rbac import Permission
from app.services.audit import record_audit_log

router = APIRouter()

@router.get("", response_model=List[ServiceProviderOut])
async def list_providers(
    category: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.NUMBERS_READ))
):
    query = select(ServiceProvider).order_by(ServiceProvider.name)
    if category and category != "ALL":
        query = query.where(ServiceProvider.category == category)
    if status and status != "ALL":
        query = query.where(ServiceProvider.status == status)

    res = await db.execute(query)
    providers = res.scalars().all()
    return providers

@router.post("", response_model=ServiceProviderOut)
async def create_provider(
    req: ServiceProviderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.PROVIDERS_MANAGE))
):
    existing = await db.execute(select(ServiceProvider).where(ServiceProvider.code == req.code.upper()))
    if existing.scalars().first():
        raise HTTPException(status_code=400, detail="Provider with this code already exists")

    provider = ServiceProvider(
        name=req.name,
        code=req.code.upper(),
        category=req.category,
        integration_type=req.integration_type,
        webhook_url=req.webhook_url,
        avg_sla_hours=req.avg_sla_hours,
        status="ACTIVE"
    )
    db.add(provider)
    await db.commit()
    await db.refresh(provider)

    await record_audit_log(
        db=db,
        actor_email=current_user.email,
        actor_role=current_user.role,
        organization_name="Platform Admin",
        action="SERVICE_PROVIDER_CREATED",
        entity_type="PROVIDER",
        entity_id=provider.id,
        details=f"Registered provider {provider.name} ({provider.code}) in category {provider.category}"
    )

    return provider

@router.patch("/{id}", response_model=ServiceProviderOut)
async def update_provider(
    id: str,
    req: ServiceProviderUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.PROVIDERS_MANAGE))
):
    res = await db.execute(select(ServiceProvider).where(ServiceProvider.id == id))
    provider = res.scalars().first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    if req.name:
        provider.name = req.name
    if req.category:
        provider.category = req.category
    if req.integration_type:
        provider.integration_type = req.integration_type
    if req.webhook_url is not None:
        provider.webhook_url = req.webhook_url
    if req.status:
        provider.status = req.status
    if req.avg_sla_hours is not None:
        provider.avg_sla_hours = req.avg_sla_hours

    provider.last_sync_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(provider)

    return provider

@router.post("/{id}/ping")
async def ping_provider(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.PROVIDERS_MANAGE))
):
    res = await db.execute(select(ServiceProvider).where(ServiceProvider.id == id))
    provider = res.scalars().first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    provider.last_sync_at = datetime.now(timezone.utc)
    await db.commit()

    return {
        "status": "HEALTHY",
        "latency_ms": 42,
        "mode": "SANDBOX_MOCK",
        "provider": provider.name,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
