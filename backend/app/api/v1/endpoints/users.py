from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.models import User, Organization
from app.schemas.schemas import UserOut, UserCreate
from app.api.deps import get_current_user, require_permission
from app.core.rbac import Permission, Role, ROLE_PERMISSIONS
from app.core.security import get_password_hash
from app.services.audit import record_audit_log

router = APIRouter()

@router.get("", response_model=List[UserOut])
async def list_users(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.USERS_MANAGE))
):
    res = await db.execute(select(User).order_by(User.created_at))
    users = res.scalars().all()
    
    out = []
    for u in users:
        org_name = None
        if u.organization_id:
            org_res = await db.execute(select(Organization).where(Organization.id == u.organization_id))
            org = org_res.scalars().first()
            if org:
                org_name = org.name

        out.append(UserOut(
            id=u.id,
            email=u.email,
            full_name=u.full_name,
            role=u.role,
            organization_id=u.organization_id,
            organization_name=org_name,
            is_active=u.is_active,
            created_at=u.created_at
        ))
    return out

@router.post("", response_model=UserOut)
async def create_user(
    req: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.USERS_MANAGE))
):
    existing = await db.execute(select(User).where(User.email == req.email))
    if existing.scalars().first():
        raise HTTPException(status_code=400, detail="User with this email already exists")

    new_user = User(
        email=req.email,
        hashed_password=get_password_hash(req.password),
        full_name=req.full_name,
        role=req.role,
        organization_id=req.organization_id,
        is_active=True
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    await record_audit_log(
        db=db,
        actor_email=current_user.email,
        actor_role=current_user.role,
        organization_name="Admin Ops",
        action="USER_ACCOUNT_CREATED",
        entity_type="USER",
        entity_id=new_user.id,
        details=f"Created user account {new_user.email} with role {new_user.role}"
    )

    return UserOut(
        id=new_user.id,
        email=new_user.email,
        full_name=new_user.full_name,
        role=new_user.role,
        organization_id=new_user.organization_id,
        is_active=new_user.is_active,
        created_at=new_user.created_at
    )

@router.get("/rbac-matrix")
async def get_rbac_matrix(
    current_user: User = Depends(get_current_user)
):
    """Returns granular permission definitions for all 7 roles"""
    matrix = {}
    for role, perms in ROLE_PERMISSIONS.items():
        matrix[role.value] = [p.value for p in perms]
    return matrix
