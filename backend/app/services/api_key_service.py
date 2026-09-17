"""
NumberGuard — API Key Management Service (Phase 3)
Secure API key generation (ng_live_ prefix), hashing, rotation, scoping, and validation.
Keys are hashed with SHA-256 before storage; the full secret is only returned on creation.
"""
from __future__ import annotations

import secrets
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.models import ApiKey, Organization


class ApiKeyService:
    @staticmethod
    def _hash_key(secret: str) -> str:
        return hashlib.sha256(secret.encode("utf-8")).hexdigest()

    @classmethod
    async def create_key(
        cls,
        db: AsyncSession,
        organization_id: str,
        name: str,
        scopes: str = "numbers:read,providers:write",
        expires_in_days: Optional[int] = 90
    ) -> Tuple[ApiKey, str]:
        """
        Generates a new API key. Returns (ApiKey model, raw_key_string).
        raw_key_string is only available ONCE at creation.
        """
        random_part = secrets.token_hex(24)
        raw_key = f"ng_live_{random_part}"
        key_prefix = raw_key[:12]
        hashed = cls._hash_key(raw_key)

        expires_at = (
            datetime.now(timezone.utc) + timedelta(days=expires_in_days)
            if expires_in_days
            else None
        )

        api_key = ApiKey(
            organization_id=organization_id,
            key_prefix=key_prefix,
            hashed_key=hashed,
            name=name,
            scopes=scopes,
            expires_at=expires_at,
            is_active=True
        )
        db.add(api_key)
        await db.commit()
        await db.refresh(api_key)

        return api_key, raw_key

    @classmethod
    async def validate_key(
        cls,
        db: AsyncSession,
        raw_key: str,
        required_scope: Optional[str] = None
    ) -> Optional[ApiKey]:
        """
        Validates an API key against database.
        Checks prefix, full hash, active state, expiration, and required scope.
        """
        if not raw_key or not raw_key.startswith("ng_live_"):
            return None

        key_prefix = raw_key[:12]
        hashed = cls._hash_key(raw_key)

        stmt = select(ApiKey).where(
            ApiKey.key_prefix == key_prefix,
            ApiKey.hashed_key == hashed,
            ApiKey.is_active == True
        )
        result = await db.execute(stmt)
        api_key = result.scalar_one_or_none()

        if not api_key:
            return None

        # Check expiration
        if api_key.expires_at and api_key.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
            return None

        # Check scope
        if required_scope:
            key_scopes = [s.strip() for s in (api_key.scopes or "").split(",") if s.strip()]
            if required_scope not in key_scopes and "admin" not in key_scopes and "*" not in key_scopes:
                return None

        # Update last_used_at
        api_key.last_used_at = datetime.now(timezone.utc)
        await db.commit()

        return api_key

    @classmethod
    async def list_keys(
        cls,
        db: AsyncSession,
        organization_id: str
    ) -> List[ApiKey]:
        """Lists all keys for an organization."""
        stmt = select(ApiKey).where(ApiKey.organization_id == organization_id).order_by(ApiKey.created_at.desc())
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @classmethod
    async def revoke_key(
        cls,
        db: AsyncSession,
        key_id: str,
        organization_id: str
    ) -> bool:
        """Revokes an API key."""
        stmt = select(ApiKey).where(
            ApiKey.id == key_id,
            ApiKey.organization_id == organization_id
        )
        res = await db.execute(stmt)
        api_key = res.scalar_one_or_none()
        if not api_key:
            return False

        api_key.is_active = False
        await db.commit()
        return True

    @classmethod
    async def rotate_key(
        cls,
        db: AsyncSession,
        key_id: str,
        organization_id: str
    ) -> Optional[Tuple[ApiKey, str]]:
        """
        Revokes old key and creates a replacement key with the same name and scopes.
        """
        stmt = select(ApiKey).where(
            ApiKey.id == key_id,
            ApiKey.organization_id == organization_id
        )
        res = await db.execute(stmt)
        old_key = res.scalar_one_or_none()
        if not old_key:
            return None

        old_key.is_active = False
        name = old_key.name
        scopes = old_key.scopes or "numbers:read,providers:write"
        await db.commit()

        return await cls.create_key(db, organization_id, name, scopes=scopes)
