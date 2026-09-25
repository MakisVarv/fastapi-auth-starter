from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from app.api.dependencies.auth import get_current_user
from app.api.dependencies.permissions import (
    get_list_permissions,
    get_permission_use_case,
)
from app.application.errors import PermissionNotFoundError
from app.domain.entities.permission import Permission
from app.domain.entities.role import Role
from app.domain.entities.user import User
from app.main import app


def make_actor(
    *,
    has_permission: bool = True,
) -> User:
    permissions = [Permission(name="permission.read")] if has_permission else []

    return User(
        first_name="Admin",
        last_name="User",
        email="admin@example.com",
        password_hash="hash",
        role=Role(
            name="Admin",
            level=100,
            permissions=permissions,
        ),
    )


class FakeListPermissions:
    def __init__(self, permissions: list[Permission]) -> None:
        self.permissions = permissions
        self.called = False

    def execute(self) -> list[Permission]:
        self.called = True
        return self.permissions


class FakeGetPermission:
    def __init__(
        self,
        *,
        permission: Permission | None = None,
        error: Exception | None = None,
    ) -> None:
        self.permission = permission
        self.error = error
        self.received_id: UUID | None = None

    def execute(self, permission_id: UUID) -> Permission:
        self.received_id = permission_id

        if self.error is not None:
            raise self.error

        assert self.permission is not None
        return self.permission


def test_list_permissions_returns_permissions(
    client: TestClient,
) -> None:
    actor = make_actor()

    permissions = [
        Permission(
            name="user.read",
            description="Read users",
        ),
        Permission(
            name="role.read",
            description="Read roles",
        ),
    ]

    fake = FakeListPermissions(permissions)

    app.dependency_overrides[get_current_user] = lambda: actor
    app.dependency_overrides[get_list_permissions] = lambda: fake

    response = client.get("/api/permissions")

    assert response.status_code == 200

    body = response.json()

    assert len(body) == 2
    assert body[0]["name"] == "user.read"
    assert body[0]["description"] == "Read users"
    assert body[1]["name"] == "role.read"

    assert fake.called is True


def test_list_permissions_requires_permission_read(
    client: TestClient,
) -> None:
    actor = make_actor(
        has_permission=False,
    )

    fake = FakeListPermissions([])

    app.dependency_overrides[get_current_user] = lambda: actor
    app.dependency_overrides[get_list_permissions] = lambda: fake

    response = client.get("/api/permissions")

    assert response.status_code == 403
    assert response.json() == {"message": "Permission denied."}

    assert fake.called is False


def test_get_permission_returns_permission(
    client: TestClient,
) -> None:
    actor = make_actor()

    permission = Permission(
        name="user.read",
        description="Read users",
    )

    fake = FakeGetPermission(
        permission=permission,
    )

    app.dependency_overrides[get_current_user] = lambda: actor
    app.dependency_overrides[get_permission_use_case] = lambda: fake

    response = client.get(f"/api/permissions/{permission.id}")

    assert response.status_code == 200

    assert response.json() == {
        "id": str(permission.id),
        "name": "user.read",
        "description": "Read users",
    }

    assert fake.received_id == permission.id


def test_get_permission_maps_missing_permission_to_not_found(
    client: TestClient,
) -> None:
    actor = make_actor()
    missing_id = uuid4()

    fake = FakeGetPermission(
        error=PermissionNotFoundError(),
    )

    app.dependency_overrides[get_current_user] = lambda: actor
    app.dependency_overrides[get_permission_use_case] = lambda: fake

    response = client.get(f"/api/permissions/{missing_id}")

    assert response.status_code == 404
    assert response.json() == {"message": "Permission not found!"}

    assert fake.received_id == missing_id


def test_get_permission_rejects_invalid_uuid(
    client: TestClient,
) -> None:
    actor = make_actor()

    app.dependency_overrides[get_current_user] = lambda: actor

    response = client.get("/api/permissions/not-a-uuid")

    assert response.status_code == 422

    assert any(error["field"] == "permission_id" for error in response.json()["errors"])
