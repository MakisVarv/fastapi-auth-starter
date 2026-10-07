import os

from alembic.config import Config

from alembic import command
from tests.integration.config import test_settings

if __name__ == "__main__":
    os.environ["DATABASE_URL"] = test_settings.TEST_DATABASE_URL

    alembic_config = Config("alembic.ini")

    command.upgrade(alembic_config, "head")

    print("Test database upgraded to head.")
