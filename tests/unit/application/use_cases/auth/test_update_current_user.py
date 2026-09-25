from typing import cast
from uuid import UUID

import pytest

from app.application.errors import UserNotFoundError
from app.application.ports.unit_of_work import UnitOfWork
from app.application.use_cases.auth.update_current_user import (
    UpdateCurrentUser,
)
from app.domain.entities.role import Role
from app.domain.entities.user import User


class FakeUserRepository:
    def __init__(self, user: User | None) -> None:
        self.user = user
        self.requested_id: UUID | None = None
        self.updated_user: User | None = None

    def get_by_id(self, user_id: UUID) -> User | None:
        self.requested_id = user_id

        if self.user is not None and self.user.id == user_id:
            return self.user

        return None

    def update(self, user: User) -> None:
        self.updated_user = user


class FakeUnitOfWork:
    def __init__(self, user: User | None) -> None:
        self.users = FakeUserRepository(user)
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


def make_user() -> User:
    return User(
        first_name="Before",
        last_name="User",
        email="user@example.com",
        phone=None,
        password_hash="hashed-password",
        role=Role(
            name="User",
            level=10,
        ),
    )


def test_update_current_user_updates_allowed_fields_and_commits() -> None:
    user = make_user()
    uow = FakeUnitOfWork(user)

    use_case = UpdateCurrentUser(
        uow=cast(UnitOfWork, uow),
    )

    result = use_case.execute(
        user_id=user.id,
        updates={
            "first_name": "After",
            "last_name": "Updated",
            "phone": "+30-123456789",
        },
    )

    assert result is user
    assert result.first_name == "After"
    assert result.last_name == "Updated"
    assert result.phone == "+30-123456789"

    assert uow.users.updated_user is user
    assert uow.committed is True


def test_update_current_user_ignores_disallowed_fields() -> None:
    user = make_user()
    original_email = user.email
    original_password_hash = user.password_hash

    uow = FakeUnitOfWork(user)

    use_case = UpdateCurrentUser(
        uow=cast(UnitOfWork, uow),
    )

    result = use_case.execute(
        user_id=user.id,
        updates={
            "first_name": "Changed",
            "email": "attacker@example.com",
            "password_hash": "changed-hash",
        },
    )

    assert result.first_name == "Changed"
    assert result.email == original_email
    assert result.password_hash == original_password_hash

    assert uow.users.updated_user is user
    assert uow.committed is True


def test_update_current_user_rejects_missing_user() -> None:
    missing_user = make_user()
    uow = FakeUnitOfWork(None)

    use_case = UpdateCurrentUser(
        uow=cast(UnitOfWork, uow),
    )

    with pytest.raises(UserNotFoundError):
        use_case.execute(
            user_id=missing_user.id,
            updates={"first_name": "Changed"},
        )

    assert uow.users.updated_user is None
    assert uow.committed is False
