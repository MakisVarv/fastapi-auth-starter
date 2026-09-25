from typing import cast
from uuid import UUID, uuid4

import pytest

from app.application.errors import (
    AuthorizationError,
    AuthorizationReason,
    DeleteRoleWithUsersError,
    ProtectedRoleDeletionError,
    RoleNotFoundError,
)
from app.application.ports.unit_of_work import UnitOfWork
from app.application.use_cases.roles.delete_role import DeleteRole
from app.domain.entities.role import Role
from app.domain.entities.user import User


class FakeRoleRepository:
    def __init__(self, role: Role | None) -> None:
        self.role = role
        self.deleted_role: Role | None = None

    def get_by_id(self, role_id: UUID) -> Role | None:
        if self.role is not None and self.role.id == role_id:
            return self.role

        return None

    def delete(self, entity: Role) -> None:
        self.deleted_role = entity


class FakeUserRepository:
    def __init__(self, role_user_count: int = 0) -> None:
        self.role_user_count = role_user_count
        self.requested_role_id: UUID | None = None

    def count_by_role(self, role_id: UUID) -> int:
        self.requested_role_id = role_id
        return self.role_user_count


class FakeUnitOfWork:
    def __init__(
        self,
        *,
        role: Role | None,
        role_user_count: int = 0,
    ) -> None:
        self.roles = FakeRoleRepository(role)
        self.users = FakeUserRepository(role_user_count)
        self.committed = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        pass

    def commit(self) -> None:
        self.committed = True


def make_actor(level: int = 80) -> User:
    return User(
        first_name="Actor",
        last_name="User",
        email="actor@example.com",
        password_hash="hash",
        role=Role(name="Manager", level=level),
    )


def test_delete_role_deletes_role_and_commits() -> None:
    actor = make_actor()

    role = Role(
        name="Support",
        level=50,
    )

    uow = FakeUnitOfWork(role=role)

    use_case = DeleteRole(uow=cast(UnitOfWork, uow))

    use_case.execute(
        actor=actor,
        role_id=role.id,
    )

    assert uow.users.requested_role_id == role.id
    assert uow.roles.deleted_role is role
    assert uow.committed is True


def test_delete_role_rejects_missing_role() -> None:
    actor = make_actor()
    missing_id = uuid4()

    uow = FakeUnitOfWork(role=None)

    use_case = DeleteRole(uow=cast(UnitOfWork, uow))

    with pytest.raises(RoleNotFoundError):
        use_case.execute(
            actor=actor,
            role_id=missing_id,
        )

    assert uow.roles.deleted_role is None
    assert uow.committed is False


def test_delete_role_rejects_actor_who_cannot_manage_role() -> None:
    actor = make_actor(level=50)

    role = Role(
        name="Support",
        level=50,
    )

    uow = FakeUnitOfWork(role=role)

    use_case = DeleteRole(uow=cast(UnitOfWork, uow))

    with pytest.raises(AuthorizationError) as exc_info:
        use_case.execute(
            actor=actor,
            role_id=role.id,
        )

    assert exc_info.value.reason == AuthorizationReason.CANNOT_MANAGE_ROLE
    assert uow.users.requested_role_id is None
    assert uow.roles.deleted_role is None
    assert uow.committed is False


def test_delete_role_rejects_protected_role() -> None:
    actor = make_actor(level=100)

    role = Role(
        name="Admin",
        level=100,
    )

    uow = FakeUnitOfWork(role=role)

    use_case = DeleteRole(uow=cast(UnitOfWork, uow))

    with pytest.raises(ProtectedRoleDeletionError):
        use_case.execute(
            actor=actor,
            role_id=role.id,
        )

    assert uow.users.requested_role_id is None
    assert uow.roles.deleted_role is None
    assert uow.committed is False


def test_delete_role_rejects_role_with_assigned_users() -> None:
    actor = make_actor()

    role = Role(
        name="Support",
        level=50,
    )

    uow = FakeUnitOfWork(
        role=role,
        role_user_count=2,
    )

    use_case = DeleteRole(uow=cast(UnitOfWork, uow))

    with pytest.raises(DeleteRoleWithUsersError):
        use_case.execute(
            actor=actor,
            role_id=role.id,
        )

    assert uow.users.requested_role_id == role.id
    assert uow.roles.deleted_role is None
    assert uow.committed is False
