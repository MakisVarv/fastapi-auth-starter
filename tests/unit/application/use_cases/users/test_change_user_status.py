from typing import cast
from uuid import UUID, uuid4

import pytest

from app.application.errors import (
    AuthorizationError,
    AuthorizationReason,
    UserNotFoundError,
)
from app.application.ports.unit_of_work import UnitOfWork
from app.application.use_cases.users.change_user_status import ChangeUserStatus
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


def make_user(
    *,
    role_level: int,
    role_name: str = "User",
    is_active: bool = True,
) -> User:
    return User(
        first_name="Test",
        last_name="User",
        email="user@example.com",
        password_hash="hash",
        is_active=is_active,
        role=Role(
            name=role_name,
            level=role_level,
        ),
    )


def test_change_user_status_updates_status_and_commits() -> None:
    actor = make_user(
        role_level=80,
        role_name="Manager",
    )

    target = make_user(
        role_level=20,
        is_active=True,
    )

    uow = FakeUnitOfWork(target)

    use_case = ChangeUserStatus(
        uow=cast(UnitOfWork, uow),
    )

    result = use_case.execute(
        actor=actor,
        user_id=target.id,
        is_active=False,
    )

    assert result is target
    assert result.is_active is False

    assert uow.users.requested_id == target.id
    assert uow.users.updated_user is target
    assert uow.committed is True


def test_change_user_status_can_activate_user() -> None:
    actor = make_user(
        role_level=80,
        role_name="Manager",
    )

    target = make_user(
        role_level=20,
        is_active=False,
    )

    uow = FakeUnitOfWork(target)

    use_case = ChangeUserStatus(
        uow=cast(UnitOfWork, uow),
    )

    result = use_case.execute(
        actor=actor,
        user_id=target.id,
        is_active=True,
    )

    assert result.is_active is True
    assert uow.users.updated_user is target
    assert uow.committed is True


def test_change_user_status_rejects_missing_user() -> None:
    actor = make_user(
        role_level=80,
        role_name="Manager",
    )

    missing_id = uuid4()

    uow = FakeUnitOfWork(None)

    use_case = ChangeUserStatus(
        uow=cast(UnitOfWork, uow),
    )

    with pytest.raises(UserNotFoundError):
        use_case.execute(
            actor=actor,
            user_id=missing_id,
            is_active=False,
        )

    assert uow.users.requested_id == missing_id
    assert uow.users.updated_user is None
    assert uow.committed is False


def test_change_user_status_rejects_actor_who_cannot_manage_user() -> None:
    actor = make_user(
        role_level=50,
        role_name="Manager",
    )

    target = make_user(
        role_level=50,
        role_name="Peer",
    )

    uow = FakeUnitOfWork(target)

    use_case = ChangeUserStatus(
        uow=cast(UnitOfWork, uow),
    )

    with pytest.raises(AuthorizationError) as exc_info:
        use_case.execute(
            actor=actor,
            user_id=target.id,
            is_active=False,
        )

    assert exc_info.value.reason == AuthorizationReason.CANNOT_MANAGE_USER

    assert target.is_active is True
    assert uow.users.updated_user is None
    assert uow.committed is False
