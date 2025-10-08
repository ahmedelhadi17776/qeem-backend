"""Token repository for refresh token management."""

import logging
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, update

from ..models.user import RefreshToken
from ..infra.redis import get_redis, is_redis_available
from ..core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class TokenRepository:
    """Repository for refresh token operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_refresh_token(
        self,
        user_id: int,
        token_hash: str,
        expires_at: datetime,
        device_info: Optional[str] = None,
        token_family: Optional[str] = None,
    ) -> RefreshToken:
        """Create a new refresh token."""
        refresh_token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            device_info=device_info,
            token_family=token_family,
        )
        self.db.add(refresh_token)
        await self.db.flush()
        await self.db.refresh(refresh_token)

        # Store in Redis for fast access
        await self._store_in_redis(refresh_token)

        return refresh_token

    async def get_by_token_hash(self, token_hash: str) -> Optional[RefreshToken]:
        """Get refresh token by hash."""
        # Try Redis first
        redis_token = await self._get_from_redis(token_hash)
        if redis_token:
            return redis_token

        # Fallback to database
        stmt = select(RefreshToken).where(
            and_(
                RefreshToken.token_hash == token_hash,
                RefreshToken.revoked.is_(False),
                RefreshToken.expires_at > datetime.utcnow(),
            )
        )
        result = await self.db.execute(stmt)
        token = result.scalar_one_or_none()

        if token:
            # Store in Redis for next time
            await self._store_in_redis(token)

        return token

    async def revoke_token(self, token_hash: str) -> bool:
        """Revoke a refresh token."""
        token = await self.get_by_token_hash(token_hash)
        if not token:
            return False

        # Update token as revoked
        await self.db.execute(
            update(RefreshToken)
            .where(RefreshToken.token_hash == token_hash)
            .values(revoked=True)
        )
        await self.db.flush()

        # Remove from Redis
        await self._remove_from_redis(token_hash)

        return True

    async def revoke_all_user_tokens(self, user_id: int) -> int:
        """Revoke all refresh tokens for a user."""
        stmt = select(RefreshToken.id, RefreshToken.token_hash).where(
            and_(RefreshToken.user_id == user_id, RefreshToken.revoked.is_(False))
        )
        result = await self.db.execute(stmt)
        tokens = result.all()

        count = 0
        for token_id, token_hash in tokens:
            await self.db.execute(
                update(RefreshToken)
                .where(RefreshToken.id == token_id)
                .values(revoked=True)
            )
            await self._remove_from_redis(token_hash)
            count += 1

        await self.db.flush()
        return count

    async def revoke_token_family(self, token_family: str) -> int:
        """Revoke all tokens in a family (for token rotation)."""
        stmt = select(RefreshToken.id, RefreshToken.token_hash).where(
            and_(
                RefreshToken.token_family == token_family,
                RefreshToken.revoked.is_(False),
            )
        )
        result = await self.db.execute(stmt)
        tokens = result.all()

        count = 0
        for token_id, token_hash in tokens:
            await self.db.execute(
                update(RefreshToken)
                .where(RefreshToken.id == token_id)
                .values(revoked=True)
            )
            await self._remove_from_redis(token_hash)
            count += 1

        await self.db.flush()
        return count

    async def cleanup_expired_tokens(self) -> int:
        """Remove expired tokens from database."""
        stmt = select(RefreshToken.id, RefreshToken.token_hash).where(
            RefreshToken.expires_at < datetime.now(timezone.utc)
        )
        result = await self.db.execute(stmt)
        expired_tokens = result.all()

        count = 0
        for token_id, token_hash in expired_tokens:
            await self.db.execute(
                update(RefreshToken)
                .where(RefreshToken.id == token_id)
                .values(revoked=True)
            )
            await self._remove_from_redis(token_hash)
            count += 1

        await self.db.flush()
        return count

    async def get_user_active_tokens(self, user_id: int) -> List[RefreshToken]:
        """Get all active tokens for a user."""
        stmt = (
            select(RefreshToken)
            .where(
                and_(
                    RefreshToken.user_id == user_id,
                    RefreshToken.revoked.is_(False),
                    RefreshToken.expires_at > datetime.utcnow(),
                )
            )
            .order_by(desc(RefreshToken.created_at))
        )

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def _store_in_redis(self, token: RefreshToken):
        """Store token metadata in Redis."""
        if not is_redis_available():
            return

        try:
            redis = get_redis()
            if redis:
                # Store token metadata with TTL
                ttl = int(
                    (token.expires_at - datetime.now(timezone.utc)).total_seconds()
                )
                if ttl > 0:
                    key = f"refresh_token:{token.token_hash}"
                    data = {
                        "user_id": token.user_id,
                        "expires_at": token.expires_at.isoformat(),
                        "device_info": token.device_info or "",
                        "token_family": token.token_family or "",
                    }
                    redis.hset(key, mapping=data)
                    redis.expire(key, ttl)
        except Exception as e:
            logger.warning(f"Failed to store token in Redis: {e}")

    async def _get_from_redis(self, token_hash: str) -> Optional[RefreshToken]:
        """Get token metadata from Redis."""
        if not is_redis_available():
            return None

        try:
            redis = get_redis()
            if redis:
                key = f"refresh_token:{token_hash}"
                data = redis.hgetall(key)
                # Handle both sync and async Redis clients
                if hasattr(data, "__await__"):
                    data = await data

                if data:
                    # Create RefreshToken object from Redis data
                    token = RefreshToken(
                        token_hash=token_hash,
                        user_id=int(data["user_id"]),
                        expires_at=datetime.fromisoformat(data["expires_at"]),
                        device_info=data.get("device_info") or None,
                        token_family=data.get("token_family") or None,
                        revoked=False,
                    )
                    return token
        except Exception as e:
            logger.warning(f"Failed to get token from Redis: {e}")

        return None

    async def _remove_from_redis(self, token_hash: str):
        """Remove token from Redis."""
        if not is_redis_available():
            return

        try:
            redis = get_redis()
            if redis:
                key = f"refresh_token:{token_hash}"
                redis.delete(key)
        except Exception as e:
            logger.warning(f"Failed to remove token from Redis: {e}")
