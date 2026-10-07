from typing import cast

import pytest

import app.application.use_cases.permissions.prune_permission as prune_module
from app.application.ports.unit_of_work import UnitOfWork
from app.application.use_cases.permissions.prune_permission import PrunePermission
from app.domain.entities.permission import Permission
from app.domain.entities.role import Role


class FakePermissionRepository:
    def __init__(
        self,
        permission: Permission | None,
    ) -> None:
        self.permission = permission
        self.requested_name: str | None = None
        self.deleted: Permission | None = None

    def get_by_name(
        self,
        name: str,
    ) -> Permission | None:
        self.requested_name = name

        if self.permission is not None and self.permission.name == name:
            return self.permission

        return None

    def delete(
        self,
        permission: Permission,
    ) -> None:
        self.deleted = permission


class FakeRoleRepository:
    def __init__(
        self,
        roles: list[Role],
    ) -> None:
        self.roles = roles
        self.removed: list[tuple[Role, Permission]] = []

    def list_all(self) -> list[Role]:
        return list(self.roles)

    def remove_permission(
        self,
        role: Role,
        permission: Permission,
    ) -> None:
        self.removed.append(
            (role, permission),
        )


class FakeUnitOfWork:
    def __init__(
        self,
        *,
        permission: Permission | None,
        roles: list[Role] | None = None,
    ) -> None:
        self.permissions = FakePermissionRepository(permission)
        self.roles = FakeRoleRepository(roles or [])

        self.commit_count = 0
        self.rollback_count = 0

    def __enter__(self):
        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ) -> None:
        if exc_type is not None:
            self.rollback()

    def commit(self) -> None:
        self.commit_count += 1

    def rollback(self) -> None:
        self.rollback_count += 1


def set_permissions_registry(
    monkeypatch: pytest.MonkeyPatch,
    permissions: list[dict[str, str]],
) -> None:
    monkeypatch.setattr(
        prune_module,
        "PERMISSIONS",
        permissions,
    )


def test_prune_rejects_registered_permission(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    set_permissions_registry(
        monkeypatch,
        [
            {
                "name": "user.read",
                "description": "Read users",
            }
        ],
    )

    permission = Permission(
        name="user.read",
        description="Read users",
    )

    uow = FakeUnitOfWork(
        permission=permission,
    )

    use_case = PrunePermission(
        uow=cast(UnitOfWork, uow),
    )

    with pytest.raises(
        ValueError,
        match="still registered",
    ):
        use_case.execute("user.read")

    assert uow.permissions.requested_name is None
    assert uow.permissions.deleted is None
    assert uow.commit_count == 0
    assert uow.rollback_count == 1


def test_prune_rejects_permission_that_does_not_exist(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    set_permissions_registry(
        monkeypatch,
        [],
    )

    uow = FakeUnitOfWork(
        permission=None,
    )

    use_case = PrunePermission(
        uow=cast(UnitOfWork, uow),
    )

    with pytest.raises(
        ValueError,
        match="does not exist",
    ):
        use_case.execute("legacy.permission")

    assert uow.permissions.requested_name == "legacy.permission"
    assert uow.permissions.deleted is None
    assert uow.commit_count == 0
    assert uow.rollback_count == 1


def test_prune_removes_permission_from_roles_deletes_and_commits(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    set_permissions_registry(
        monkeypatch,
        [
            {
                "name": "user.read",
                "description": "Read users",
            }
        ],
    )

    stale_permission = Permission(
        name="legacy.permission",
        description="Old permission",
    )

    admin_role = Role(
        name="Admin",
        level=100,
        permissions=[stale_permission],
    )

    manager_role = Role(
        name="Manager",
        level=50,
        permissions=[stale_permission],
    )

    user_role = Role(
        name="User",
        level=10,
        permissions=[],
    )

    uow = FakeUnitOfWork(
        permission=stale_permission,
        roles=[
            admin_role,
            manager_role,
            user_role,
        ],
    )

    use_case = PrunePermission(
        uow=cast(UnitOfWork, uow),
    )

    use_case.execute("legacy.permission")

    assert stale_permission not in admin_role.permissions
    assert stale_permission not in manager_role.permissions
    assert user_role.permissions == []

    assert uow.roles.removed == [
        (admin_role, stale_permission),
        (manager_role, stale_permission),
    ]

    assert uow.permissions.deleted is stale_permission

    assert uow.commit_count == 1
    assert uow.rollback_count == 0
