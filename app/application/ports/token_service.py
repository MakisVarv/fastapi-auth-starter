from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True)
class IssuedRefreshToken:
    token: str
    jti: str
    expires_at: datetime


@dataclass(frozen=True)
class RefreshTokenClaims:
    user_id: UUID
    session_id: UUID
    jti: str


class TokenService(Protocol):
    def create_access_token(self, user_id: UUID) -> str: ...

    def create_refresh_token(
        self,
        user_id: UUID,
        session_id: UUID,
    ) -> IssuedRefreshToken: ...

    def decode_refresh_token(self, token: str) -> RefreshTokenClaims: ...
