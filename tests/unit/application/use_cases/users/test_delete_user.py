from typing import cast
from uuid import UUID, uuid4

import pytest

from app.application.errors import (
    ActiveUserDeletionError,
    AuthorizationError,
    AuthorizationReason,
    UserNotFoundError,
)
from app.application.ports.unit_of_work import UnitOfWork
from app.application.use_cases.users.delete_user import DeleteUser
from app.domain.entities.role import Role
from app.domain.entities.user import User


class FakeUserRepository:
    def __init__(self, user: User | None) -> None:
        self.user = user
        self.requested_id: UUID | None = None
        self.deleted_user: User | None = None

    def get_by_id(self, user_id: UUID) -> User | None:
        self.requested_id = user_id

        if self.user is not None and self.user.id == user_id:
            return self.user

        return None

    def delete(self, entity: User) -> None:
        self.deleted_user = entity


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


def test_delete_user_deletes_inactive_user_and_commits() -> None:
    actor = make_user(
        role_level=80,
        role_name="Manager",
    )

    target = make_user(
        role_level=20,
        is_active=False,
    )

    uow = FakeUnitOfWork(target)

    use_case = DeleteUser(
        uow=cast(UnitOfWork, uow),
    )

    use_case.execute(
        actor=actor,
        user_id=target.id,
    )

    assert uow.users.requested_id == target.id
    assert uow.users.deleted_user is target
    assert uow.committed is True


def test_delete_user_rejects_missing_user() -> None:
    actor = make_user(
        role_level=80,
        role_name="Manager",
    )

    missing_id = uuid4()

    uow = FakeUnitOfWork(None)

    use_case = DeleteUser(
        uow=cast(UnitOfWork, uow),
    )

    with pytest.raises(UserNotFoundError):
        use_case.execute(
            actor=actor,
            user_id=missing_id,
        )

    assert uow.users.requested_id == missing_id
    assert uow.users.deleted_user is None
    assert uow.committed is False


def test_delete_user_rejects_actor_who_cannot_manage_user() -> None:
    actor = make_user(
        role_level=50,
        role_name="Manager",
    )

    target = make_user(
        role_level=50,
        role_name="Peer",
        is_active=False,
    )

    uow = FakeUnitOfWork(target)

    use_case = DeleteUser(
        uow=cast(UnitOfWork, uow),
    )

    with pytest.raises(AuthorizationError) as exc_info:
        use_case.execute(
            actor=actor,
            user_id=target.id,
        )

    assert exc_info.value.reason == AuthorizationReason.CANNOT_MANAGE_USER

    assert uow.users.deleted_user is None
    assert uow.committed is False


def test_delete_user_rejects_active_user() -> None:
    actor = make_user(
        role_level=80,
        role_name="Manager",
    )

    target = make_user(
        role_level=20,
        is_active=True,
    )

    uow = FakeUnitOfWork(target)

    use_case = DeleteUser(
        uow=cast(UnitOfWork, uow),
    )

    with pytest.raises(ActiveUserDeletionError):
        use_case.execute(
            actor=actor,
            user_id=target.id,
        )

    assert uow.users.deleted_user is None
    assert uow.committed is False
