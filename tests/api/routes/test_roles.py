from typing import Any
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from app.api.dependencies.auth import get_current_user
from app.api.dependencies.roles import (
    get_assign_permission,
    get_create_role,
    get_delete_role,
    get_list_roles,
    get_remove_permission,
    get_role_use_case,
    get_update_role,
)
from app.application.errors import (
    PermissionAlreadyInRoleError,
    ProtectedRoleDeletionError,
    RoleAlreadyExist,
    RoleNotFoundError,
)
from app.domain.entities.permission import Permission
from app.domain.entities.role import Role
from app.domain.entities.user import User
from app.main import app


def make_actor(
    *,
    permissions: list[str] | None = None,
) -> User:
    return User(
        first_name="Admin",
        last_name="User",
        email="admin@example.com",
        password_hash="hash",
        role=Role(
            name="Admin",
            level=100,
            permissions=[Permission(name=name) for name in (permissions or [])],
        ),
    )


def make_admin() -> User:
    return make_actor(
        permissions=[
            "role.read",
            "role.create",
            "role.update",
            "role.delete",
            "role.assign_permission",
        ]
    )


def make_role(
    *,
    name: str = "Support",
    level: int = 40,
    description: str | None = "Support role",
    permissions: list[Permission] | None = None,
) -> Role:
    return Role(
        name=name,
        level=level,
        description=description,
        permissions=permissions or [],
    )


class FakeListRoles:
    def __init__(self, roles: list[Role]) -> None:
        self.roles = roles
        self.called = False

    def execute(self) -> list[Role]:
        self.called = True
        return self.roles


class FakeGetRole:
    def __init__(
        self,
        *,
        role: Role | None = None,
        error: Exception | None = None,
    ) -> None:
        self.role = role
        self.error = error
        self.received_id: UUID | None = None

    def execute(self, role_id: UUID) -> Role:
        self.received_id = role_id

        if self.error is not None:
            raise self.error

        assert self.role is not None
        return self.role


class FakeCreateRole:
    def __init__(
        self,
        *,
        role: Role | None = None,
        error: Exception | None = None,
    ) -> None:
        self.role = role
        self.error = error
        self.received: dict[str, Any] | None = None

    def execute(
        self,
        *,
        actor: User,
        name: str,
        description: str | None,
        level: int,
    ) -> Role:
        self.received = {
            "actor": actor,
            "name": name,
            "description": description,
            "level": level,
        }

        if self.error is not None:
            raise self.error

        assert self.role is not None
        return self.role


class FakeUpdateRole:
    def __init__(
        self,
        *,
        role: Role | None = None,
        error: Exception | None = None,
    ) -> None:
        self.role = role
        self.error = error
        self.received_actor: User | None = None
        self.received_role_id: UUID | None = None
        self.received_updates: dict[str, Any] | None = None

    def execute(
        self,
        *,
        actor: User,
        role_id: UUID,
        updates: dict[str, Any],
    ) -> Role:
        self.received_actor = actor
        self.received_role_id = role_id
        self.received_updates = updates

        if self.error is not None:
            raise self.error

        assert self.role is not None
        return self.role


class FakeDeleteRole:
    def __init__(
        self,
        *,
        error: Exception | None = None,
    ) -> None:
        self.error = error
        self.received_actor: User | None = None
        self.received_role_id: UUID | None = None

    def execute(
        self,
        *,
        actor: User,
        role_id: UUID,
    ) -> None:
        self.received_actor = actor
        self.received_role_id = role_id

        if self.error is not None:
            raise self.error


class FakeAssignPermission:
    def __init__(
        self,
        *,
        role: Role | None = None,
        error: Exception | None = None,
    ) -> None:
        self.role = role
        self.error = error
        self.received_actor: User | None = None
        self.received_role_id: UUID | None = None
        self.received_permission_id: UUID | None = None

    def execute(
        self,
        *,
        actor: User,
        role_id: UUID,
        permission_id: UUID,
    ) -> Role:
        self.received_actor = actor
        self.received_role_id = role_id
        self.received_permission_id = permission_id

        if self.error is not None:
            raise self.error

        assert self.role is not None
        return self.role


class FakeRemovePermission:
    def __init__(self) -> None:
        self.received_actor: User | None = None
        self.received_role_id: UUID | None = None
        self.received_permission_id: UUID | None = None

    def execute(
        self,
        *,
        actor: User,
        role_id: UUID,
        permission_id: UUID,
    ) -> None:
        self.received_actor = actor
        self.received_role_id = role_id
        self.received_permission_id = permission_id


def test_list_roles_returns_roles(
    client: TestClient,
) -> None:
    actor = make_admin()

    roles = [
        make_role(name="Admin", level=100),
        make_role(name="User", level=10),
    ]

    fake = FakeListRoles(roles)

    app.dependency_overrides[get_current_user] = lambda: actor
    app.dependency_overrides[get_list_roles] = lambda: fake

    response = client.get("/api/roles")

    assert response.status_code == 200

    body = response.json()

    assert len(body) == 2
    assert body[0]["name"] == "Admin"
    assert body[1]["name"] == "User"

    assert fake.called is True


def test_list_roles_requires_role_read_permission(
    client: TestClient,
) -> None:
    actor = make_actor()

    fake = FakeListRoles([])

    app.dependency_overrides[get_current_user] = lambda: actor
    app.dependency_overrides[get_list_roles] = lambda: fake

    response = client.get("/api/roles")

    assert response.status_code == 403
    assert response.json() == {"message": "Permission denied."}

    assert fake.called is False


def test_get_role_returns_role(
    client: TestClient,
) -> None:
    actor = make_admin()
    role = make_role()

    fake = FakeGetRole(role=role)

    app.dependency_overrides[get_current_user] = lambda: actor
    app.dependency_overrides[get_role_use_case] = lambda: fake

    response = client.get(f"/api/roles/{role.id}")

    assert response.status_code == 200
    assert response.json()["id"] == str(role.id)
    assert response.json()["name"] == "Support"

    assert fake.received_id == role.id


def test_get_role_maps_missing_role_to_not_found(
    client: TestClient,
) -> None:
    actor = make_admin()
    missing_id = uuid4()

    fake = FakeGetRole(
        error=RoleNotFoundError(),
    )

    app.dependency_overrides[get_current_user] = lambda: actor
    app.dependency_overrides[get_role_use_case] = lambda: fake

    response = client.get(f"/api/roles/{missing_id}")

    assert response.status_code == 404
    assert response.json() == {"message": "Role not found!"}


def test_create_role_returns_created_role_and_forwards_payload(
    client: TestClient,
) -> None:
    actor = make_admin()

    role = make_role(
        name="Support",
        level=40,
        description="Support team",
    )

    fake = FakeCreateRole(role=role)

    app.dependency_overrides[get_current_user] = lambda: actor
    app.dependency_overrides[get_create_role] = lambda: fake

    response = client.post(
        "/api/roles",
        json={
            "name": "  Support  ",
            "description": "Support team",
            "level": 40,
        },
    )

    assert response.status_code == 201

    assert response.json()["id"] == str(role.id)
    assert response.json()["name"] == "Support"

    assert fake.received == {
        "actor": actor,
        "name": "Support",
        "description": "Support team",
        "level": 40,
    }


def test_create_role_rejects_invalid_level(
    client: TestClient,
) -> None:
    actor = make_admin()

    app.dependency_overrides[get_current_user] = lambda: actor

    response = client.post(
        "/api/roles",
        json={
            "name": "Support",
            "level": 101,
        },
    )

    assert response.status_code == 422

    assert any(error["field"] == "level" for error in response.json()["errors"])


def test_create_role_maps_duplicate_name_to_conflict(
    client: TestClient,
) -> None:
    actor = make_admin()

    fake = FakeCreateRole(
        error=RoleAlreadyExist(),
    )

    app.dependency_overrides[get_current_user] = lambda: actor
    app.dependency_overrides[get_create_role] = lambda: fake

    response = client.post(
        "/api/roles",
        json={
            "name": "Support",
            "level": 40,
        },
    )

    assert response.status_code == 409
    assert response.json() == {"message": "Role already exists."}


def test_update_role_forwards_only_provided_fields(
    client: TestClient,
) -> None:
    actor = make_admin()

    role = make_role(
        name="Updated Support",
        level=40,
    )

    fake = FakeUpdateRole(role=role)

    app.dependency_overrides[get_current_user] = lambda: actor
    app.dependency_overrides[get_update_role] = lambda: fake

    response = client.patch(
        f"/api/roles/{role.id}",
        json={
            "name": "  Updated Support  ",
        },
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Updated Support"

    assert fake.received_actor is actor
    assert fake.received_role_id == role.id
    assert fake.received_updates == {"name": "Updated Support"}


def test_update_role_rejects_empty_payload(
    client: TestClient,
) -> None:
    actor = make_admin()

    app.dependency_overrides[get_current_user] = lambda: actor

    response = client.patch(
        f"/api/roles/{uuid4()}",
        json={},
    )

    assert response.status_code == 422

    assert any(
        error["message"] == "At least one field must be provided."
        for error in response.json()["errors"]
    )


def test_delete_role_returns_no_content(
    client: TestClient,
) -> None:
    actor = make_admin()
    role_id = uuid4()

    fake = FakeDeleteRole()

    app.dependency_overrides[get_current_user] = lambda: actor
    app.dependency_overrides[get_delete_role] = lambda: fake

    response = client.delete(f"/api/roles/{role_id}")

    assert response.status_code == 204
    assert response.content == b""

    assert fake.received_actor is actor
    assert fake.received_role_id == role_id


def test_delete_role_maps_protected_role_to_conflict(
    client: TestClient,
) -> None:
    actor = make_admin()
    role_id = uuid4()

    fake = FakeDeleteRole(
        error=ProtectedRoleDeletionError(),
    )

    app.dependency_overrides[get_current_user] = lambda: actor
    app.dependency_overrides[get_delete_role] = lambda: fake

    response = client.delete(f"/api/roles/{role_id}")

    assert response.status_code == 409
    assert response.json() == {"message": "Built-in roles cannot be deleted."}


def test_assign_permission_returns_updated_role(
    client: TestClient,
) -> None:
    actor = make_admin()

    permission = Permission(
        name="user.read",
    )

    role = make_role(
        permissions=[permission],
    )

    fake = FakeAssignPermission(role=role)

    app.dependency_overrides[get_current_user] = lambda: actor
    app.dependency_overrides[get_assign_permission] = lambda: fake

    response = client.post(
        f"/api/roles/{role.id}/permissions",
        json={
            "permission_id": str(permission.id),
        },
    )

    assert response.status_code == 201

    assert response.json()["permissions"][0]["id"] == str(permission.id)
    assert response.json()["permissions"][0]["name"] == "user.read"

    assert fake.received_actor is actor
    assert fake.received_role_id == role.id
    assert fake.received_permission_id == permission.id


def test_assign_permission_maps_duplicate_assignment_to_conflict(
    client: TestClient,
) -> None:
    actor = make_admin()

    role_id = uuid4()
    permission_id = uuid4()

    fake = FakeAssignPermission(
        error=PermissionAlreadyInRoleError(),
    )

    app.dependency_overrides[get_current_user] = lambda: actor
    app.dependency_overrides[get_assign_permission] = lambda: fake

    response = client.post(
        f"/api/roles/{role_id}/permissions",
        json={
            "permission_id": str(permission_id),
        },
    )

    assert response.status_code == 409
    assert response.json() == {"message": "Permission already assigned to role."}


def test_remove_permission_returns_no_content(
    client: TestClient,
) -> None:
    actor = make_admin()

    role_id = uuid4()
    permission_id = uuid4()

    fake = FakeRemovePermission()

    app.dependency_overrides[get_current_user] = lambda: actor
    app.dependency_overrides[get_remove_permission] = lambda: fake

    response = client.delete(f"/api/roles/{role_id}/permissions/{permission_id}")

    assert response.status_code == 204
    assert response.content == b""

    assert fake.received_actor is actor
    assert fake.received_role_id == role_id
    assert fake.received_permission_id == permission_id
