from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import jwt

from app.application.errors import InvalidAccessTokenError, InvalidRefreshTokenError
from app.application.ports.token_service import (
    AccessTokenClaims,
    IssuedRefreshToken,
    RefreshTokenClaims,
)
from app.infrastructure.config import settings


class PyJWTTokenService:
    def create_access_token(self, user_id: UUID) -> str:
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRES_MINUTES)
        payload = {
            "sub": str(user_id),
            "type": "access",
            "exp": expires_at,
        }
        return jwt.encode(
            payload,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )

    def create_refresh_token(
        self, user_id: UUID, session_id: UUID
    ) -> IssuedRefreshToken:

        jti = str(uuid4())
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRES_DAYS)
        payload = {
            "sub": str(user_id),
            "sid": str(session_id),
            "jti": jti,
            "type": "refresh",
            "exp": expires_at,
        }
        token = jwt.encode(
            payload,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )
        return IssuedRefreshToken(
            token=token,
            jti=jti,
            expires_at=expires_at,
        )

    def decode_refresh_token(self, token: str) -> RefreshTokenClaims:
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM],
            )
        except jwt.InvalidTokenError as exc:
            raise InvalidRefreshTokenError() from exc
        if payload.get("type") != "refresh":
            raise InvalidRefreshTokenError()
        try:
            user_id = UUID(payload["sub"])
            session_id = UUID(payload["sid"])
            jti = payload["jti"]
        except (KeyError, ValueError, TypeError) as exc:
            raise InvalidRefreshTokenError() from exc
        return RefreshTokenClaims(
            user_id=user_id,
            session_id=session_id,
            jti=jti,
        )

    def decode_access_token(self, token: str) -> AccessTokenClaims:
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM],
            )
        except jwt.InvalidTokenError as exc:
            raise InvalidAccessTokenError() from exc
        if payload.get("type") != "access":
            raise InvalidAccessTokenError()
        try:
            user_id = UUID(payload["sub"])
        except (KeyError, ValueError, TypeError) as exc:
            raise InvalidAccessTokenError() from exc

        return AccessTokenClaims(user_id)
