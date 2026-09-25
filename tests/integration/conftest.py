from sqlalchemy import create_engine

from tests.integration.config import test_settings

test_engine = create_engine(test_settings.TEST_DATABASE_URL)
