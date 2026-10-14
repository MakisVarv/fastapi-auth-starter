from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    SMTP_HOST: str
    SMTP_PORT: int
    SMTP_SENDER_EMAIL: str

    SMTP_USERNAME: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_USE_STARTTLS: bool = True

    FRONTEND_RESET_URL: str
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRES_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRES_DAYS: int = 7
    COOKIE_SECURE: bool = True
    CSRF_SECRET_KEY: str

    FRONTEND_ORIGIN: str

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()  # pyright: ignore[reportCallIssue]
