from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt

from app.infrastructure.config import settings


class PyJWTTokenService:
    def create_access_token(self, user_id: UUID) -> str:
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRES_MINUTES)
        payload = {
            "sub": str(user_id),
            "exp": expires_at,
        }
        return jwt.encode(
            payload,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )
