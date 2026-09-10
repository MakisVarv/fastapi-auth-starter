from typing import Protocol
from uuid import UUID

from app.domain.entities.auth_session import AuthSession


class AuthSessionRepository(Protocol):
    def get_by_id(self, session_id: UUID) -> AuthSession | None: ...

    def add(self, auth_session: AuthSession) -> None: ...
