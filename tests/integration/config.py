from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import create_engine


class TestSettings(BaseSettings):
    TEST_DATABASE_URL: str

    model_config = SettingsConfigDict(
        env_file=".env.test",
        extra="ignore",
    )


test_settings = TestSettings()  # pyright: ignore[reportCallIssue]
test_engine = create_engine(test_settings.TEST_DATABASE_URL)
