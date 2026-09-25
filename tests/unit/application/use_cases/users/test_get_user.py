from typing import cast
from uuid import UUID, uuid4

import pytest

from app.application.errors import UserNotFoundError
from app.application.ports.unit_of_work import UnitOfWork
from app.application.use_cases.users.get_user import GetUser
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


def make_user() -> User:
    return User(
        first_name="Test",
        last_name="User",
        email="user@example.com",
        password_hash="hash",
        role=Role(
            name="User",
            level=10,
        ),
    )


def test_get_user_returns_user() -> None:
    user = make_user()
    uow = FakeUnitOfWork(user)

    use_case = GetUser(
        uow=cast(UnitOfWork, uow),
    )

    result = use_case.execute(user.id)

    assert result is user
    assert uow.users.requested_id == user.id


def test_get_user_rejects_missing_user() -> None:
    missing_id = uuid4()

    uow = FakeUnitOfWork(None)

    use_case = GetUser(
        uow=cast(UnitOfWork, uow),
    )

    with pytest.raises(UserNotFoundError):
        use_case.execute(missing_id)

    assert uow.users.requested_id == missing_id
