import json
from datetime import datetime, timezone
from typing import List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload
from app.db.session import get_db
from app.models.models import Organization, User, DecommissionedNumber, ServiceProvider, AuditLog
from app.schemas.schemas import (
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationOut,
    UserOut
)
from app.api.deps import get_current_user, require_permission
from app.core.rbac import Permission, Role, get_role_permissions
from app.services.audit import record_audit_log

router = APIRouter()

def _parse_modules(val: Any) -> List[str]:
    if not val:
        return []
    if isinstance(val, list):
        return val
    if isinstance(val, str):
        try:
            parsed = json.loads(val)
            if isinstance(parsed, list):
                return parsed
        except Exception:
            return [v.strip() for v in val.split(",") if v.strip()]
    return []

@router.get("", response_model=List[OrganizationOut])
async def list_organizations(
    org_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.ORGANIZATION_MANAGE))
):
    """
    Super Admin / Auditor endpoint to inspect all enrolled B2B organizations.
    """
    query = select(Organization).options(
        selectinload(Organization.users)
    ).order_by(Organization.name)

    if org_type and org_type != "ALL":
        query = query.where(Organization.org_type == org_type)
    if is_active is not None:
        query = query.where(Organization.is_active == is_active)

    query = query.offset(skip).limit(limit)
    res = await db.execute(query)
    orgs = res.scalars().all()

    out = []
    for org in orgs:
        num_count = 0
        if org.org_type in ["TELECOM", "PLATFORM"]:
            num_res = await db.execute(
                select(func.count(DecommissionedNumber.id)).where(
                    DecommissionedNumber.organization_id == org.id
                )
            )
            num_count = num_res.scalar() or 0

        out.append(OrganizationOut(
            id=org.id,
            name=org.name,
            org_type=org.org_type,
            domain=org.domain,
            primary_contact=org.primary_contact,
            country_code=org.country_code or "IN",
            is_active=org.is_active,
            allowed_modules=_parse_modules(org.allowed_modules),
            created_at=org.created_at,
            updated_at=org.updated_at or org.created_at,
            user_count=len(org.users) if org.users else 0,
            number_count=num_count
        ))
    return out

@router.post("", response_model=OrganizationOut)
async def create_organization(
    req: OrganizationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.ORGANIZATION_MANAGE))
):
    """
    Enrolls a new B2B organization tenant.
    """
    existing = await db.execute(select(Organization).where(Organization.name == req.name))
    if existing.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Organization with name '{req.name}' already exists"
        )

    org = Organization(
        name=req.name,
        org_type=req.org_type,
        domain=req.domain,
        primary_contact=req.primary_contact,
        country_code=req.country_code,
        is_active=True,
        allowed_modules=req.allowed_modules or []
    )
    db.add(org)
    await db.commit()
    await db.refresh(org)

    # If organization is a service provider, ensure ServiceProvider record exists
    if req.org_type in ["BANK", "FINTECH", "ECOMMERCE", "MOBILITY"]:
        prov_res = await db.execute(select(ServiceProvider).where(ServiceProvider.name == req.name))
        if not prov_res.scalars().first():
            code = req.name.upper().replace(" ", "_")[:16]
            prov = ServiceProvider(
                name=req.name,
                code=code,
                category=req.org_type,
                organization_id=org.id,
                webhook_url=f"https://api.{req.domain or 'partner.internal'}/v1/numberguard-webhook",
                is_active=True
            )
            db.add(prov)
            await db.commit()

    await record_audit_log(
        db=db,
        actor_email=current_user.email,
        actor_role=current_user.role,
        organization_name=current_user.organization.name if current_user.organization else "NumberGuard Platform",
        action="ORGANIZATION_ENROLLED",
        entity_type="ORGANIZATION",
        entity_id=org.id,
        details=f"Enrolled new organization: {org.name} ({org.org_type})"
    )

    return OrganizationOut(
        id=org.id,
        name=org.name,
        org_type=org.org_type,
        domain=org.domain,
        primary_contact=org.primary_contact,
        country_code=org.country_code,
        is_active=org.is_active,
        allowed_modules=org.allowed_modules or [],
        created_at=org.created_at,
        updated_at=org.updated_at,
        user_count=0,
        number_count=0
    )

@router.get("/{id}", response_model=OrganizationOut)
async def get_organization(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Tenant authorization check
    if current_user.role not in [Role.SUPER_ADMIN.value, Role.AUDITOR.value, Role.ANALYST.value]:
        if current_user.organization_id != id:
            raise HTTPException(status_code=403, detail="Cannot access other organizations' details")

    query = select(Organization).options(selectinload(Organization.users)).where(Organization.id == id)
    res = await db.execute(query)
    org = res.scalars().first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    num_res = await db.execute(
        select(func.count(DecommissionedNumber.id)).where(DecommissionedNumber.organization_id == org.id)
    )
    num_count = num_res.scalar() or 0

    return OrganizationOut(
        id=org.id,
        name=org.name,
        org_type=org.org_type,
        domain=org.domain,
        primary_contact=org.primary_contact,
        country_code=org.country_code or "IN",
        is_active=org.is_active,
        allowed_modules=_parse_modules(org.allowed_modules),
        created_at=org.created_at,
        updated_at=org.updated_at or org.created_at,
        user_count=len(org.users) if org.users else 0,
        number_count=num_count
    )

@router.patch("/{id}", response_model=OrganizationOut)
async def update_organization(
    id: str,
    req: OrganizationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.ORGANIZATION_MANAGE))
):
    query = select(Organization).options(selectinload(Organization.users)).where(Organization.id == id)
    res = await db.execute(query)
    org = res.scalars().first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    if req.name is not None:
        org.name = req.name
    if req.org_type is not None:
        org.org_type = req.org_type
    if req.domain is not None:
        org.domain = req.domain
    if req.primary_contact is not None:
        org.primary_contact = req.primary_contact
    if req.is_active is not None:
        org.is_active = req.is_active
    if req.allowed_modules is not None:
        org.allowed_modules = json.dumps(req.allowed_modules)

    org.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(org)

    await record_audit_log(
        db=db,
        actor_email=current_user.email,
        actor_role=current_user.role,
        organization_name=current_user.organization.name if current_user.organization else "NumberGuard Platform",
        action="ORGANIZATION_UPDATED",
        entity_type="ORGANIZATION",
        entity_id=org.id,
        details=f"Updated organization {org.name}"
    )

    return OrganizationOut(
        id=org.id,
        name=org.name,
        org_type=org.org_type,
        domain=org.domain,
        primary_contact=org.primary_contact,
        country_code=org.country_code or "IN",
        is_active=org.is_active,
        allowed_modules=_parse_modules(org.allowed_modules),
        created_at=org.created_at,
        updated_at=org.updated_at,
        user_count=len(org.users) if org.users else 0,
        number_count=0
    )

@router.get("/{id}/users", response_model=List[UserOut])
async def get_organization_users(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in [Role.SUPER_ADMIN.value, Role.AUDITOR.value]:
        if current_user.organization_id != id:
            raise HTTPException(status_code=403, detail="Cannot access other organizations' users")

    query = select(User).options(selectinload(User.organization)).where(User.organization_id == id)
    res = await db.execute(query)
    users = res.scalars().all()

    return [
        UserOut(
            id=u.id,
            email=u.email,
            full_name=u.full_name,
            role=u.role,
            organization_id=u.organization_id,
            organization_name=u.organization.name if u.organization else None,
            organization_type=u.organization.org_type if u.organization else None,
            permissions=get_role_permissions(u.role),
            is_active=u.is_active,
            created_at=u.created_at
        )
        for u in users
    ]
