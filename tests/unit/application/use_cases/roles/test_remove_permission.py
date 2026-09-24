from typing import cast
from uuid import UUID

import pytest

from app.application.errors import (
    AuthorizationError,
    AuthorizationReason,
    PermissionNotFoundError,
    PermissionNotInRoleError,
    RoleNotFoundError,
)
from app.application.ports.unit_of_work import UnitOfWork
from app.application.use_cases.roles.remove_permission import RemovePermission
from app.domain.entities.permission import Permission
from app.domain.entities.role import Role
from app.domain.entities.user import User


class FakeRoleRepository:
    def __init__(self, role: Role | None) -> None:
        self.role = role
        self.removed_permission_id: UUID | None = None

    def get_by_id(self, role_id: UUID) -> Role | None:
        if self.role is not None and self.role.id == role_id:
            return self.role

        return None

    def remove_permission(
        self,
        role: Role,
        permission: Permission,
    ) -> None:
        self.removed_permission_id = permission.id


class FakePermissionRepository:
    def __init__(self, permission: Permission | None) -> None:
        self.permission = permission

    def get_by_id(
        self,
        permission_id: UUID,
    ) -> Permission | None:
        if self.permission is not None and self.permission.id == permission_id:
            return self.permission

        return None


class FakeUnitOfWork:
    def __init__(
        self,
        role: Role | None,
        permission: Permission | None,
    ) -> None:
        self.roles = FakeRoleRepository(role)
        self.permissions = FakePermissionRepository(permission)
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


def make_actor(level: int = 80) -> User:
    role = Role(
        name="Manager",
        level=level,
    )

    return User(
        first_name="Admin",
        last_name="User",
        email="admin@example.com",
        password_hash="hashed-password",
        role=role,
    )


def test_remove_permission_removes_permission_and_commits() -> None:
    actor = make_actor()

    assigned_permission = Permission(
        name="user.read",
        description="Original description",
    )

    target_role = Role(
        name="Support",
        level=50,
        permissions=[assigned_permission],
    )

    same_permission = Permission(
        id=assigned_permission.id,
        name="user.read",
        description="Different description",
    )

    uow = FakeUnitOfWork(
        role=target_role,
        permission=same_permission,
    )

    use_case = RemovePermission(
        uow=cast(UnitOfWork, uow),
    )

    use_case.execute(
        actor=actor,
        role_id=target_role.id,
        permission_id=same_permission.id,
    )

    assert not any(
        existing.id == same_permission.id for existing in target_role.permissions
    )

    assert uow.roles.removed_permission_id == same_permission.id
    assert uow.committed is True


def test_remove_permission_rejects_missing_role() -> None:
    actor = make_actor()

    permission = Permission(
        name="user.read",
    )

    missing_role = Role(
        name="Missing",
        level=50,
    )

    uow = FakeUnitOfWork(
        role=None,
        permission=permission,
    )

    use_case = RemovePermission(
        uow=cast(UnitOfWork, uow),
    )

    with pytest.raises(RoleNotFoundError):
        use_case.execute(
            actor=actor,
            role_id=missing_role.id,
            permission_id=permission.id,
        )

    assert uow.roles.removed_permission_id is None
    assert uow.committed is False


def test_remove_permission_rejects_actor_who_cannot_manage_role() -> None:
    actor = make_actor(level=50)

    permission = Permission(
        name="user.read",
    )

    target_role = Role(
        name="Support",
        level=50,
        permissions=[permission],
    )

    uow = FakeUnitOfWork(
        role=target_role,
        permission=permission,
    )

    use_case = RemovePermission(
        uow=cast(UnitOfWork, uow),
    )

    with pytest.raises(AuthorizationError) as exc_info:
        use_case.execute(
            actor=actor,
            role_id=target_role.id,
            permission_id=permission.id,
        )

    assert exc_info.value.reason == AuthorizationReason.CANNOT_MANAGE_ROLE
    assert uow.roles.removed_permission_id is None
    assert uow.committed is False


def test_remove_permission_rejects_missing_permission() -> None:
    actor = make_actor()

    assigned_permission = Permission(
        name="user.read",
    )

    target_role = Role(
        name="Support",
        level=50,
        permissions=[assigned_permission],
    )

    missing_permission = Permission(
        name="missing.permission",
    )

    uow = FakeUnitOfWork(
        role=target_role,
        permission=None,
    )

    use_case = RemovePermission(
        uow=cast(UnitOfWork, uow),
    )

    with pytest.raises(PermissionNotFoundError):
        use_case.execute(
            actor=actor,
            role_id=target_role.id,
            permission_id=missing_permission.id,
        )

    assert len(target_role.permissions) == 1
    assert uow.roles.removed_permission_id is None
    assert uow.committed is False


def test_remove_permission_rejects_permission_not_assigned_to_role() -> None:
    actor = make_actor()

    assigned_permission = Permission(
        name="user.read",
    )

    permission_to_remove = Permission(
        name="user.update",
    )

    target_role = Role(
        name="Support",
        level=50,
        permissions=[assigned_permission],
    )

    uow = FakeUnitOfWork(
        role=target_role,
        permission=permission_to_remove,
    )

    use_case = RemovePermission(
        uow=cast(UnitOfWork, uow),
    )

    with pytest.raises(PermissionNotInRoleError):
        use_case.execute(
            actor=actor,
            role_id=target_role.id,
            permission_id=permission_to_remove.id,
        )

    assert len(target_role.permissions) == 1
    assert target_role.permissions[0].id == assigned_permission.id
    assert uow.roles.removed_permission_id is None
    assert uow.committed is False
