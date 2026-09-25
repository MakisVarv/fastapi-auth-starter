from typing import cast
from uuid import UUID

import pytest

from app.application.errors import InactiveUserError, InvalidAccessTokenError
from app.application.ports.token_service import (
    AccessTokenClaims,
    TokenService,
)
from app.application.ports.unit_of_work import UnitOfWork
from app.application.use_cases.auth.get_current_user import GetCurrentUser
from app.domain.entities.role import Role
from app.domain.entities.user import User


class FakeUserRepository:
    def __init__(self, user: User | None) -> None:
        self.user = user
        self.requested_id: UUID | None = None

    def get_by_id(self, user_id: UUID) -> User | None:
        self.requested_id = user_id

        if self.user is not None and self.user.id == user_id:
            return self.user

        return None


class FakeUnitOfWork:
    def __init__(self, user: User | None) -> None:
        self.users = FakeUserRepository(user)

    def __enter__(self):
        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ) -> None:
        pass


class FakeTokenService:
    def __init__(self, claims: AccessTokenClaims) -> None:
        self.claims = claims
        self.decoded_token: str | None = None

    def decode_access_token(self, token: str) -> AccessTokenClaims:
        self.decoded_token = token
        return self.claims

    def create_access_token(self, user_id: UUID) -> str:
        raise NotImplementedError

    def create_refresh_token(self, user_id: UUID, session_id: UUID):
        raise NotImplementedError

    def decode_refresh_token(self, token: str):
        raise NotImplementedError


def make_user(*, is_active: bool = True) -> User:
    return User(
        first_name="Test",
        last_name="User",
        email="user@example.com",
        password_hash="hashed-password",
        is_active=is_active,
        role=Role(
            name="User",
            level=10,
        ),
    )


def test_get_current_user_returns_active_user() -> None:
    user = make_user()

    uow = FakeUnitOfWork(user)
    token_service = FakeTokenService(AccessTokenClaims(user_id=user.id))

    use_case = GetCurrentUser(
        uow=cast(UnitOfWork, uow),
        token_service=cast(TokenService, token_service),
    )

    result = use_case.execute("access-token")

    assert result is user
    assert token_service.decoded_token == "access-token"
    assert uow.users.requested_id == user.id


def test_get_current_user_rejects_missing_user() -> None:
    user = make_user()

    uow = FakeUnitOfWork(None)
    token_service = FakeTokenService(AccessTokenClaims(user_id=user.id))

    use_case = GetCurrentUser(
        uow=cast(UnitOfWork, uow),
        token_service=cast(TokenService, token_service),
    )

    with pytest.raises(InvalidAccessTokenError):
        use_case.execute("access-token")

    assert uow.users.requested_id == user.id


def test_get_current_user_rejects_inactive_user() -> None:
    user = make_user(is_active=False)

    uow = FakeUnitOfWork(user)
    token_service = FakeTokenService(AccessTokenClaims(user_id=user.id))

    use_case = GetCurrentUser(
        uow=cast(UnitOfWork, uow),
        token_service=cast(TokenService, token_service),
    )

    with pytest.raises(InactiveUserError):
        use_case.execute("access-token")
