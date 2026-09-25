from collections.abc import Generator
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.domain.entities.role import Role
from app.infrastructure.repositories.auth_session_repository import (
    SqlAlchemyAuthSessionRepository,
)
from app.infrastructure.repositories.permission_repository import (
    SqlAlchemyPermissionRepository,
)
from app.infrastructure.repositories.role_repository import (
    SqlAlchemyRoleRepository,
)
from app.infrastructure.repositories.user_repository import (
    SqlAlchemyUserRepository,
)
from app.infrastructure.uow.sqlalchemy import SqlAlchemyUnitOfWork
from tests.integration.config import test_settings

test_engine = create_engine(
    test_settings.TEST_DATABASE_URL,
)


@pytest.fixture
def uow_session_factory() -> Generator[sessionmaker[Session], None, None]:
    connection = test_engine.connect()
    transaction = connection.begin()

    factory = sessionmaker(
        bind=connection,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )

    try:
        yield factory
    finally:
        transaction.rollback()
        connection.close()


def make_role() -> Role:
    return Role(
        name=f"UOW-{uuid4().hex[:8]}",
        level=25,
    )


def test_enter_creates_repositories_using_same_session(
    uow_session_factory: sessionmaker[Session],
) -> None:
    with SqlAlchemyUnitOfWork(uow_session_factory) as uow:
        assert isinstance(
            uow.users,
            SqlAlchemyUserRepository,
        )
        assert isinstance(
            uow.roles,
            SqlAlchemyRoleRepository,
        )
        assert isinstance(
            uow.permissions,
            SqlAlchemyPermissionRepository,
        )
        assert isinstance(
            uow.auth_sessions,
            SqlAlchemyAuthSessionRepository,
        )

        assert uow.users.session is uow.session
        assert uow.roles.session is uow.session
        assert uow.permissions.session is uow.session
        assert uow.auth_sessions.session is uow.session


def test_commit_persists_changes(
    uow_session_factory: sessionmaker[Session],
) -> None:
    role = make_role()

    with SqlAlchemyUnitOfWork(uow_session_factory) as uow:
        uow.roles.add(role)
        uow.commit()

    with uow_session_factory() as verification_session:
        repository = SqlAlchemyRoleRepository(
            verification_session,
        )

        persisted = repository.get_by_name(
            role.name,
        )

        assert persisted is not None
        assert persisted.id == role.id
        assert persisted.name == role.name
        assert persisted.level == role.level


def test_exit_without_commit_rolls_back_changes(
    uow_session_factory: sessionmaker[Session],
) -> None:
    role = make_role()

    with SqlAlchemyUnitOfWork(uow_session_factory) as uow:
        uow.roles.add(role)

        # Force the INSERT to reach PostgreSQL before leaving
        # the transaction, proving rollback rather than merely
        # discarding an unflushed object.
        uow.session.flush()

    with uow_session_factory() as verification_session:
        repository = SqlAlchemyRoleRepository(
            verification_session,
        )

        persisted = repository.get_by_name(
            role.name,
        )

        assert persisted is None


def test_exception_rolls_back_changes(
    uow_session_factory: sessionmaker[Session],
) -> None:
    role = make_role()

    with pytest.raises(RuntimeError):
        with SqlAlchemyUnitOfWork(uow_session_factory) as uow:
            uow.roles.add(role)
            uow.session.flush()

            raise RuntimeError("Simulated failure")

    with uow_session_factory() as verification_session:
        repository = SqlAlchemyRoleRepository(
            verification_session,
        )

        persisted = repository.get_by_name(
            role.name,
        )

        assert persisted is None
