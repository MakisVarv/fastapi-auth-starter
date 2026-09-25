from pydantic_settings import BaseSettings, SettingsConfigDict


class TestSettings(BaseSettings):
    TEST_DATABASE_URL: str

    model_config = SettingsConfigDict(
        env_file=".env.test",
        extra="ignore",
    )


test_settings = TestSettings()  # pyright: ignore[reportCallIssue]
