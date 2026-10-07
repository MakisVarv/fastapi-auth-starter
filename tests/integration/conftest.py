from collections.abc import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

import app.infrastructure.models  # noqa: F401
from app.application.use_cases.permissions.sync_permissions import SyncPermissions
from app.infrastructure.database.base import Base
from app.infrastructure.uow.sqlalchemy import SqlAlchemyUnitOfWork
from scripts.seed import seed_roles
from tests.integration.config import test_settings

test_engine = create_engine(test_settings.TEST_DATABASE_URL)


TestSessionFactory = sessionmaker(
    bind=test_engine,
    expire_on_commit=False,
)


@pytest.fixture(scope="session", autouse=True)
def setup_database() -> None:
    Base.metadata.create_all(test_engine)

    with TestSessionFactory() as session:
        seed_roles(session)

    uow = SqlAlchemyUnitOfWork(TestSessionFactory)
    result = SyncPermissions(uow).execute()

    if result.stale:
        raise RuntimeError(f"Stale permissions detected: {', '.join(result.stale)}")


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    connection = test_engine.connect()
    transaction = connection.begin()

    session = Session(
        bind=connection,
        join_transaction_mode="create_savepoint",
        expire_on_commit=False,
    )

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()
