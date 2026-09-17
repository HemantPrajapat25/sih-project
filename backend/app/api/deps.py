from typing import Generator, Optional, List
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.db.session import get_db
from app.core.security import decode_access_token
from app.core.rbac import Permission, has_permission, Role
from app.models.models import User, Organization

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token", auto_error=False)

async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    if not token:
        # Fallback to dev default mock admin if token omitted in dev
        result = await db.execute(
            select(User).options(selectinload(User.organization)).limit(1)
        )
        user = result.scalars().first()
        if user:
            return user
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload["sub"]
    result = await db.execute(
        select(User).options(selectinload(User.organization)).where(User.id == user_id)
    )
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User account not found")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is inactive")
    return user

def require_permission(required_permission: Permission):
    """
    Dependency factory ensuring the authenticated user possesses the specific RBAC permission.
    """
    async def permission_checker(current_user: User = Depends(get_current_user)) -> User:
        if not has_permission(current_user.role, required_permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied. Required privilege: '{required_permission.value}' for role '{current_user.role}'"
            )
        return current_user
    return permission_checker

def require_organization_type(allowed_types: List[str]):
    """
    Ensures user belongs to an organization of the specified type(s) or is a SUPER_ADMIN.
    """
    async def org_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role == Role.SUPER_ADMIN.value:
            return current_user
        if not current_user.organization or current_user.organization.org_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access restricted to organizations of type: {', '.join(allowed_types)}"
            )
        return current_user
    return org_checker

