"""
NumberGuard — API Keys API Endpoints (Phase 3)
Allows organization administrators to generate, view, rotate, and revoke programmatic API keys.
"""
from __future__ import annotations

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.models import User
from app.api.deps import get_current_user, require_permission
from app.core.rbac import Permission
from app.services.api_key_service import ApiKeyService

router = APIRouter()


class ApiKeyCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=64, description="Friendly label for this key")
    scopes: str = Field("numbers:read,providers:write", description="Comma-separated scopes")
    expires_in_days: Optional[int] = Field(90, ge=1, le=365)


class ApiKeyOut(BaseModel):
    id: str
    organization_id: str
    name: str
    key_prefix: str
    scopes: Optional[str] = None
    is_active: bool
    created_at: datetime
    last_used_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ApiKeyCreatedOut(ApiKeyOut):
    raw_key: str = Field(..., description="Full secret key — displayed ONLY once at creation")


@router.get("", response_model=List[ApiKeyOut])
async def list_api_keys(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.SETTINGS_MANAGE)),
):
    """
    List all API keys for the user's organization.
    Secret tokens are never returned in this endpoint.
    """
    return await ApiKeyService.list_keys(db, current_user.organization_id)


@router.post("", response_model=ApiKeyCreatedOut, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    payload: ApiKeyCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.SETTINGS_MANAGE)),
):
    """
    Generate a new API key.
    IMPORTANT: The `raw_key` in the response is shown ONLY once. Store it securely.
    """
    api_key, raw_key = await ApiKeyService.create_key(
        db=db,
        organization_id=current_user.organization_id,
        name=payload.name,
        scopes=payload.scopes,
        expires_in_days=payload.expires_in_days
    )
    res = ApiKeyCreatedOut(
        id=api_key.id,
        organization_id=api_key.organization_id,
        name=api_key.name,
        key_prefix=api_key.key_prefix,
        scopes=api_key.scopes,
        is_active=api_key.is_active,
        created_at=api_key.created_at,
        last_used_at=api_key.last_used_at,
        expires_at=api_key.expires_at,
        raw_key=raw_key
    )
    return res


@router.post("/{key_id}/rotate", response_model=ApiKeyCreatedOut)
async def rotate_api_key(
    key_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.SETTINGS_MANAGE)),
):
    """
    Invalidates the specified key and generates a new key with identical permissions.
    """
    result = await ApiKeyService.rotate_key(db, key_id, current_user.organization_id)
    if not result:
        raise HTTPException(status_code=404, detail="API key not found")
    new_key, raw_key = result
    return ApiKeyCreatedOut(
        id=new_key.id,
        organization_id=new_key.organization_id,
        name=new_key.name,
        key_prefix=new_key.key_prefix,
        scopes=new_key.scopes,
        is_active=new_key.is_active,
        created_at=new_key.created_at,
        last_used_at=new_key.last_used_at,
        expires_at=new_key.expires_at,
        raw_key=raw_key
    )


@router.delete("/{key_id}", status_code=status.HTTP_200_OK)
async def revoke_api_key(
    key_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.SETTINGS_MANAGE)),
):
    """
    Revoke an active API key immediately.
    """
    success = await ApiKeyService.revoke_key(db, key_id, current_user.organization_id)
    if not success:
        raise HTTPException(status_code=404, detail="API key not found")
    return {"status": "ok", "message": "API key revoked successfully"}
