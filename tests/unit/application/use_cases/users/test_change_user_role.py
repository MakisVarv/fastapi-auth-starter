from typing import cast
from uuid import UUID, uuid4

import pytest

from app.application.errors import (
    AuthorizationError,
    AuthorizationReason,
    RoleNotFoundError,
    UserNotFoundError,
)
from app.application.ports.unit_of_work import UnitOfWork
from app.application.use_cases.users.change_user_role import ChangeUserRole
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


class FakeRoleRepository:
    def __init__(self, role: Role | None) -> None:
        self.role = role
        self.requested_id: UUID | None = None

    def get_by_id(self, role_id: UUID) -> Role | None:
        self.requested_id = role_id

        if self.role is not None and self.role.id == role_id:
            return self.role

        return None


class FakeUnitOfWork:
    def __init__(
        self,
        *,
        user: User | None,
        role: Role | None,
    ) -> None:
        self.users = FakeUserRepository(user)
        self.roles = FakeRoleRepository(role)
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
) -> User:
    return User(
        first_name="Test",
        last_name="User",
        email="user@example.com",
        password_hash="hash",
        role=Role(
            name=role_name,
            level=role_level,
        ),
    )


def test_change_user_role_updates_role_and_commits() -> None:
    actor = make_user(
        role_level=80,
        role_name="Manager",
    )

    target = make_user(
        role_level=20,
        role_name="User",
    )

    new_role = Role(
        name="Support",
        level=40,
    )

    uow = FakeUnitOfWork(
        user=target,
        role=new_role,
    )

    use_case = ChangeUserRole(
        uow=cast(UnitOfWork, uow),
    )

    result = use_case.execute(
        actor=actor,
        user_id=target.id,
        role_id=new_role.id,
    )

    assert result is target
    assert result.role is new_role

    assert uow.users.requested_id == target.id
    assert uow.roles.requested_id == new_role.id
    assert uow.users.updated_user is target
    assert uow.committed is True


def test_change_user_role_rejects_missing_user() -> None:
    actor = make_user(
        role_level=80,
        role_name="Manager",
    )

    role = Role(
        name="Support",
        level=40,
    )

    missing_user_id = uuid4()

    uow = FakeUnitOfWork(
        user=None,
        role=role,
    )

    use_case = ChangeUserRole(
        uow=cast(UnitOfWork, uow),
    )

    with pytest.raises(UserNotFoundError):
        use_case.execute(
            actor=actor,
            user_id=missing_user_id,
            role_id=role.id,
        )

    assert uow.roles.requested_id is None
    assert uow.users.updated_user is None
    assert uow.committed is False


def test_change_user_role_rejects_actor_who_cannot_manage_user() -> None:
    actor = make_user(
        role_level=50,
        role_name="Manager",
    )

    target = make_user(
        role_level=50,
        role_name="Peer",
    )

    new_role = Role(
        name="Support",
        level=20,
    )

    uow = FakeUnitOfWork(
        user=target,
        role=new_role,
    )

    use_case = ChangeUserRole(
        uow=cast(UnitOfWork, uow),
    )

    with pytest.raises(AuthorizationError) as exc_info:
        use_case.execute(
            actor=actor,
            user_id=target.id,
            role_id=new_role.id,
        )

    assert exc_info.value.reason == AuthorizationReason.CANNOT_MANAGE_USER

    assert uow.roles.requested_id is None
    assert uow.users.updated_user is None
    assert uow.committed is False


def test_change_user_role_rejects_missing_role() -> None:
    actor = make_user(
        role_level=80,
        role_name="Manager",
    )

    target = make_user(
        role_level=20,
        role_name="User",
    )

    missing_role_id = uuid4()

    uow = FakeUnitOfWork(
        user=target,
        role=None,
    )

    use_case = ChangeUserRole(
        uow=cast(UnitOfWork, uow),
    )

    with pytest.raises(RoleNotFoundError):
        use_case.execute(
            actor=actor,
            user_id=target.id,
            role_id=missing_role_id,
        )

    assert uow.roles.requested_id == missing_role_id
    assert uow.users.updated_user is None
    assert uow.committed is False


def test_change_user_role_rejects_role_actor_cannot_assign() -> None:
    actor = make_user(
        role_level=60,
        role_name="Manager",
    )

    target = make_user(
        role_level=20,
        role_name="User",
    )

    new_role = Role(
        name="Senior Manager",
        level=60,
    )

    uow = FakeUnitOfWork(
        user=target,
        role=new_role,
    )

    use_case = ChangeUserRole(
        uow=cast(UnitOfWork, uow),
    )

    with pytest.raises(AuthorizationError) as exc_info:
        use_case.execute(
            actor=actor,
            user_id=target.id,
            role_id=new_role.id,
        )

    assert exc_info.value.reason == AuthorizationReason.CANNOT_ASSIGN_ROLE

    assert target.role.name == "User"
    assert uow.users.updated_user is None
    assert uow.committed is False
