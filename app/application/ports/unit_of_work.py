from typing import Protocol, Self

from app.application.ports.auth_session_repository import AuthSessionRepository
from app.application.ports.user_repository import UserRepository


class UnitOfWork(Protocol):
    users: UserRepository
    auth_sessions: AuthSessionRepository

    def __enter__(self) -> Self: ...

    def __exit__(self, exc_type, exc_value, traceback) -> None: ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...
