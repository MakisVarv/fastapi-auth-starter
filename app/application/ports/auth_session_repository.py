from datetime import datetime
from typing import Protocol
from uuid import UUID

from app.domain.entities.auth_session import AuthSession


class AuthSessionRepository(Protocol):
    def get_by_id(self, session_id: UUID) -> AuthSession | None: ...

    def add(self, auth_session: AuthSession) -> None: ...

    def update(self, auth_session: AuthSession) -> None: ...

    def revoke_all_for_user(
        self,
        user_id: UUID,
        revoked_at: datetime,
    ) -> None: ...
