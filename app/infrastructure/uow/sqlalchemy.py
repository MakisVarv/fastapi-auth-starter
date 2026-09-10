from typing import Self

from sqlalchemy.orm import sessionmaker

from app.application.ports.auth_session_repository import AuthSessionRepository
from app.application.ports.user_repository import UserRepository
from app.infrastructure.repositories.auth_session_repository import (
    SqlAlchemyAuthSessionRepository,
)
from app.infrastructure.repositories.user_repository import SqlAlchemyUserRepository


class SqlAlchemyUnitOfWork:
    users: UserRepository
    auth_sessions: AuthSessionRepository

    def __init__(self, session_factory: sessionmaker) -> None:
        self.session_factory = session_factory

    def __enter__(self) -> Self:
        self.session = self.session_factory()
        self.users = SqlAlchemyUserRepository(self.session)
        self.auth_sessions = SqlAlchemyAuthSessionRepository(self.session)
        return self

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.rollback()
        self.session.close()
