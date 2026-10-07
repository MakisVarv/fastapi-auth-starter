from typing import cast

import pytest

import app.application.use_cases.permissions.sync_permissions as sync_module
from app.application.ports.unit_of_work import UnitOfWork
from app.application.use_cases.permissions.sync_permissions import SyncPermissions
from app.domain.entities.permission import Permission
from app.domain.entities.role import Role


class FakePermissionRepository:
    def __init__(
        self,
        permissions: list[Permission] | None = None,
    ) -> None:
        self.permissions = permissions or []
        self.added: list[Permission] = []
        self.updated: list[Permission] = []

    def list_all(self) -> list[Permission]:
        return list(self.permissions)

    def add(self, permission: Permission) -> None:
        self.permissions.append(permission)
        self.added.append(permission)

    def update(self, permission: Permission) -> None:
        self.updated.append(permission)


class FakeRoleRepository:
    def __init__(
        self,
        admin_role: Role | None,
    ) -> None:
        self.admin_role = admin_role
        self.assigned: list[tuple[Role, Permission]] = []

    def get_by_name(self, name: str) -> Role | None:
        if self.admin_role is not None and self.admin_role.name == name:
            return self.admin_role

        return None

    def assign_permission(
        self,
        role: Role,
        permission: Permission,
    ) -> None:
        self.assigned.append((role, permission))


class FakeUnitOfWork:
    def __init__(
        self,
        *,
        permissions: list[Permission] | None = None,
        admin_role: Role | None,
    ) -> None:
        self.permissions = FakePermissionRepository(permissions)
        self.roles = FakeRoleRepository(admin_role)

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
        sync_module,
        "PERMISSIONS",
        permissions,
    )


def test_sync_creates_missing_permission_and_assigns_it_to_admin(
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

    admin_role = Role(
        name="Admin",
        level=100,
    )

    uow = FakeUnitOfWork(
        permissions=[],
        admin_role=admin_role,
    )

    use_case = SyncPermissions(
        uow=cast(UnitOfWork, uow),
    )

    result = use_case.execute()

    assert result.created == ["user.read"]
    assert result.updated == []
    assert result.unchanged == []
    assert result.stale == []

    assert len(uow.permissions.added) == 1

    created_permission = uow.permissions.added[0]

    assert created_permission.name == "user.read"
    assert created_permission.description == "Read users"

    assert created_permission in admin_role.permissions

    assert uow.roles.assigned == [
        (admin_role, created_permission),
    ]

    assert uow.commit_count == 1


def test_sync_updates_changed_permission_description(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    set_permissions_registry(
        monkeypatch,
        [
            {
                "name": "user.read",
                "description": "Read user information",
            }
        ],
    )

    persisted_permission = Permission(
        name="user.read",
        description="Old description",
    )

    admin_role = Role(
        name="Admin",
        level=100,
        permissions=[persisted_permission],
    )

    uow = FakeUnitOfWork(
        permissions=[persisted_permission],
        admin_role=admin_role,
    )

    use_case = SyncPermissions(
        uow=cast(UnitOfWork, uow),
    )

    result = use_case.execute()

    assert result.created == []
    assert result.updated == ["user.read"]
    assert result.unchanged == []
    assert result.stale == []

    assert persisted_permission.description == "Read user information"

    assert uow.permissions.updated == [
        persisted_permission,
    ]

    assert uow.permissions.added == []
    assert uow.roles.assigned == []

    assert uow.commit_count == 1


def test_sync_reports_unchanged_permission(
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

    persisted_permission = Permission(
        name="user.read",
        description="Read users",
    )

    admin_role = Role(
        name="Admin",
        level=100,
        permissions=[persisted_permission],
    )

    uow = FakeUnitOfWork(
        permissions=[persisted_permission],
        admin_role=admin_role,
    )

    use_case = SyncPermissions(
        uow=cast(UnitOfWork, uow),
    )

    result = use_case.execute()

    assert result.created == []
    assert result.updated == []
    assert result.unchanged == ["user.read"]
    assert result.stale == []

    assert uow.permissions.added == []
    assert uow.permissions.updated == []
    assert uow.roles.assigned == []

    assert uow.commit_count == 1


def test_sync_reports_stale_permission_without_deleting_it(
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

    configured_permission = Permission(
        name="user.read",
        description="Read users",
    )

    stale_permission = Permission(
        name="legacy.permission",
        description="Old permission",
    )

    admin_role = Role(
        name="Admin",
        level=100,
        permissions=[configured_permission],
    )

    uow = FakeUnitOfWork(
        permissions=[
            configured_permission,
            stale_permission,
        ],
        admin_role=admin_role,
    )

    use_case = SyncPermissions(
        uow=cast(UnitOfWork, uow),
    )

    result = use_case.execute()

    assert result.created == []
    assert result.updated == []
    assert result.unchanged == ["user.read"]
    assert result.stale == ["legacy.permission"]

    assert stale_permission in uow.permissions.permissions

    assert uow.permissions.added == []
    assert uow.permissions.updated == []

    assert uow.commit_count == 1


def test_sync_assigns_existing_permission_missing_from_admin(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    set_permissions_registry(
        monkeypatch,
        [
            {
                "name": "dashboard.read",
                "description": "View dashboard",
            }
        ],
    )

    persisted_permission = Permission(
        name="dashboard.read",
        description="View dashboard",
    )

    admin_role = Role(
        name="Admin",
        level=100,
        permissions=[],
    )

    uow = FakeUnitOfWork(
        permissions=[persisted_permission],
        admin_role=admin_role,
    )

    use_case = SyncPermissions(
        uow=cast(UnitOfWork, uow),
    )

    result = use_case.execute()

    assert result.created == []
    assert result.updated == []
    assert result.unchanged == ["dashboard.read"]
    assert result.stale == []

    assert admin_role.permissions == [
        persisted_permission,
    ]

    assert uow.roles.assigned == [
        (admin_role, persisted_permission),
    ]

    assert uow.commit_count == 1


def test_sync_is_idempotent(
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

    admin_role = Role(
        name="Admin",
        level=100,
    )

    uow = FakeUnitOfWork(
        permissions=[],
        admin_role=admin_role,
    )

    use_case = SyncPermissions(
        uow=cast(UnitOfWork, uow),
    )

    first_result = use_case.execute()
    second_result = use_case.execute()

    assert first_result.created == ["user.read"]
    assert first_result.unchanged == []

    assert second_result.created == []
    assert second_result.updated == []
    assert second_result.unchanged == ["user.read"]
    assert second_result.stale == []

    assert len(uow.permissions.added) == 1
    assert len(uow.roles.assigned) == 1

    assert uow.commit_count == 2


def test_sync_raises_when_admin_role_does_not_exist(
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

    uow = FakeUnitOfWork(
        permissions=[],
        admin_role=None,
    )

    use_case = SyncPermissions(
        uow=cast(UnitOfWork, uow),
    )

    with pytest.raises(
        RuntimeError,
        match="Admin role does not exist",
    ):
        use_case.execute()

    assert uow.commit_count == 0
    assert uow.rollback_count == 1
