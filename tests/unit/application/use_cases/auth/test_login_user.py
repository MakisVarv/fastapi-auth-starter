from datetime import datetime, timedelta, timezone
from typing import cast
from uuid import UUID

import pytest

from app.application.errors import InactiveUserError, InvalidCredentialsError
from app.application.ports.password_hasher import PasswordHasher
from app.application.ports.token_service import IssuedRefreshToken, TokenService
from app.application.ports.unit_of_work import UnitOfWork
from app.application.use_cases.auth.login_user import LoginUser
from app.domain.entities.auth_session import AuthSession
from app.domain.entities.role import Role
from app.domain.entities.user import User


class FakeUserRepository:
    def __init__(self, user: User | None) -> None:
        self.user = user
        self.requested_email: str | None = None

    def get_by_email(self, email: str) -> User | None:
        self.requested_email = email

        if self.user is not None and self.user.email == email:
            return self.user

        return None


class FakeAuthSessionRepository:
    def __init__(self) -> None:
        self.added_session: AuthSession | None = None

    def add(self, auth_session: AuthSession) -> None:
        self.added_session = auth_session


class FakeUnitOfWork:
    def __init__(self, user: User | None) -> None:
        self.users = FakeUserRepository(user)
        self.auth_sessions = FakeAuthSessionRepository()
        self.committed = False

    def __enter__(self):
        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ) -> None:
        pass

    def commit(self) -> None:
        self.committed = True


class FakePasswordHasher:
    def __init__(self, verification_result: bool = True) -> None:
        self.verification_result = verification_result
        self.verify_calls: list[tuple[str, str]] = []

    def hash(self, password: str) -> str:
        return f"hashed:{password}"

    def verify(
        self,
        password: str,
        password_hash: str,
    ) -> bool:
        self.verify_calls.append((password, password_hash))
        return self.verification_result


class FakeTokenService:
    def __init__(self) -> None:
        self.access_token_user_id: UUID | None = None
        self.refresh_token_user_id: UUID | None = None
        self.refresh_token_session_id: UUID | None = None

        self.refresh_expires_at = datetime.now(timezone.utc) + timedelta(days=7)

    def create_access_token(self, user_id: UUID) -> str:
        self.access_token_user_id = user_id
        return "access-token"

    def create_refresh_token(
        self,
        user_id: UUID,
        session_id: UUID,
    ) -> IssuedRefreshToken:
        self.refresh_token_user_id = user_id
        self.refresh_token_session_id = session_id

        return IssuedRefreshToken(
            token="refresh-token",
            jti="refresh-jti",
            expires_at=self.refresh_expires_at,
        )

    def decode_refresh_token(self, token: str):
        raise NotImplementedError

    def decode_access_token(self, token: str):
        raise NotImplementedError


def make_user(
    *,
    email: str = "user@example.com",
    password_hash: str = "hashed-password",
    is_active: bool = True,
) -> User:
    role = Role(
        name="User",
        level=10,
    )

    return User(
        first_name="Test",
        last_name="User",
        email=email,
        password_hash=password_hash,
        is_active=is_active,
        role=role,
    )


def test_login_creates_tokens_session_and_commits() -> None:
    user = make_user()

    uow = FakeUnitOfWork(user)
    password_hasher = FakePasswordHasher()
    token_service = FakeTokenService()

    use_case = LoginUser(
        uow=cast(UnitOfWork, uow),
        password_hasher=cast(PasswordHasher, password_hasher),
        token_service=cast(TokenService, token_service),
    )

    result = use_case.execute(
        email="user@example.com",
        password="plain-password",
    )

    assert result.user is user
    assert result.access_token == "access-token"
    assert result.refresh_token == "refresh-token"

    assert password_hasher.verify_calls == [("plain-password", "hashed-password")]

    assert token_service.access_token_user_id == user.id
    assert token_service.refresh_token_user_id == user.id

    assert token_service.refresh_token_session_id is not None

    added_session = uow.auth_sessions.added_session
    assert added_session is not None

    assert added_session.id == token_service.refresh_token_session_id
    assert added_session.user_id == user.id
    assert added_session.current_refresh_jti == "refresh-jti"
    assert added_session.expires_at == token_service.refresh_expires_at
    assert added_session.revoked_at is None

    assert uow.committed is True


def test_login_normalizes_email_before_lookup() -> None:
    user = make_user(email="user@example.com")

    uow = FakeUnitOfWork(user)
    password_hasher = FakePasswordHasher()
    token_service = FakeTokenService()

    use_case = LoginUser(
        uow=cast(UnitOfWork, uow),
        password_hasher=cast(PasswordHasher, password_hasher),
        token_service=cast(TokenService, token_service),
    )

    use_case.execute(
        email="  USER@EXAMPLE.COM  ",
        password="plain-password",
    )

    assert uow.users.requested_email == "user@example.com"


def test_login_rejects_missing_user() -> None:
    uow = FakeUnitOfWork(user=None)
    password_hasher = FakePasswordHasher()
    token_service = FakeTokenService()

    use_case = LoginUser(
        uow=cast(UnitOfWork, uow),
        password_hasher=cast(PasswordHasher, password_hasher),
        token_service=cast(TokenService, token_service),
    )

    with pytest.raises(InvalidCredentialsError):
        use_case.execute(
            email="missing@example.com",
            password="plain-password",
        )

    assert password_hasher.verify_calls == []
    assert token_service.access_token_user_id is None
    assert token_service.refresh_token_user_id is None
    assert uow.auth_sessions.added_session is None
    assert uow.committed is False


def test_login_rejects_invalid_password() -> None:
    user = make_user()

    uow = FakeUnitOfWork(user)
    password_hasher = FakePasswordHasher(
        verification_result=False,
    )
    token_service = FakeTokenService()

    use_case = LoginUser(
        uow=cast(UnitOfWork, uow),
        password_hasher=cast(PasswordHasher, password_hasher),
        token_service=cast(TokenService, token_service),
    )

    with pytest.raises(InvalidCredentialsError):
        use_case.execute(
            email="user@example.com",
            password="wrong-password",
        )

    assert password_hasher.verify_calls == [("wrong-password", "hashed-password")]

    assert token_service.access_token_user_id is None
    assert token_service.refresh_token_user_id is None
    assert uow.auth_sessions.added_session is None
    assert uow.committed is False


def test_login_rejects_inactive_user() -> None:
    user = make_user(is_active=False)

    uow = FakeUnitOfWork(user)
    password_hasher = FakePasswordHasher()
    token_service = FakeTokenService()

    use_case = LoginUser(
        uow=cast(UnitOfWork, uow),
        password_hasher=cast(PasswordHasher, password_hasher),
        token_service=cast(TokenService, token_service),
    )

    with pytest.raises(InactiveUserError):
        use_case.execute(
            email="user@example.com",
            password="plain-password",
        )

    assert password_hasher.verify_calls == [("plain-password", "hashed-password")]

    assert token_service.access_token_user_id is None
    assert token_service.refresh_token_user_id is None
    assert uow.auth_sessions.added_session is None
    assert uow.committed is False
