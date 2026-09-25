import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.infrastructure.models  # noqa: F401
from app.infrastructure.database.base import Base
from scripts.seed import seed_permissions, seed_role_permissions, seed_roles
from tests.integration.config import test_settings

test_engine = create_engine(test_settings.TEST_DATABASE_URL)


TestSessionFactory = sessionmaker(
    bind=test_engine,
    expire_on_commit=False,
)


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    Base.metadata.create_all(test_engine)

    with TestSessionFactory() as session:
        seed_permissions(session)
        seed_roles(session)
        seed_role_permissions(session)
