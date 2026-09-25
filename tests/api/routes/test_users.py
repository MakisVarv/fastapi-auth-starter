from typing import Any
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from app.api.dependencies.auth import get_current_user
from app.api.dependencies.users import (
    get_change_role,
    get_change_status,
    get_create_user,
    get_delete_user,
    get_list_users,
    get_update_user,
    get_user_use_case,
)
from app.application.common.pagination import Page
from app.application.errors import (
    ActiveUserDeletionError,
    AuthorizationError,
    AuthorizationReason,
    UserNotFoundError,
)
from app.domain.entities.permission import Permission
from app.domain.entities.role import Role
from app.domain.entities.user import User
from app.main import app


def make_user(
    *,
    first_name: str = "Alice",
    last_name: str = "Stone",
    email: str = "alice@example.com",
    role_name: str = "User",
    role_level: int = 10,
    permissions: list[str] | None = None,
    is_active: bool = True,
) -> User:
    role_permissions = [Permission(name=name) for name in (permissions or [])]

    return User(
        first_name=first_name,
        last_name=last_name,
        email=email,
        password_hash="hashed-password",
        is_active=is_active,
        role=Role(
            name=role_name,
            level=role_level,
            permissions=role_permissions,
        ),
    )


def make_admin() -> User:
    return make_user(
        first_name="Admin",
        email="admin@example.com",
        role_name="Admin",
        role_level=100,
        permissions=[
            "user.read",
            "user.create",
            "user.update",
            "user.change_role",
            "user.delete",
        ],
    )


class FakeListUsers:
    def __init__(self, result: Page[User]) -> None:
        self.result = result
        self.received: dict[str, Any] | None = None

    def execute(
        self,
        *,
        page: int,
        page_size: int,
        sort_options,
        search: str | None,
        role: str | None,
        is_active: bool | None,
    ) -> Page[User]:
        self.received = {
            "page": page,
            "page_size": page_size,
            "sort_options": sort_options,
            "search": search,
            "role": role,
            "is_active": is_active,
        }

        return self.result


class FakeGetUser:
    def __init__(
        self,
        *,
        user: User | None = None,
        error: Exception | None = None,
    ) -> None:
        self.user = user
        self.error = error
        self.received_id: UUID | None = None

    def execute(self, user_id: UUID) -> User:
        self.received_id = user_id

        if self.error is not None:
            raise self.error

        assert self.user is not None
        return self.user


class FakeCreateUser:
    def __init__(self, user: User) -> None:
        self.user = user
        self.received: dict[str, Any] | None = None

    def execute(
        self,
        *,
        actor: User,
        first_name: str,
        last_name: str,
        email: str,
        password: str,
        role_id: UUID,
        phone: str | None = None,
    ) -> User:
        self.received = {
            "actor": actor,
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "password": password,
            "role_id": role_id,
            "phone": phone,
        }

        return self.user


class FakeUpdateUser:
    def __init__(
        self,
        *,
        user: User | None = None,
        error: Exception | None = None,
    ) -> None:
        self.user = user
        self.error = error
        self.received_actor: User | None = None
        self.received_user_id: UUID | None = None
        self.received_updates: dict[str, Any] | None = None

    def execute(
        self,
        *,
        actor: User,
        user_id: UUID,
        updates: dict[str, Any],
    ) -> User:
        self.received_actor = actor
        self.received_user_id = user_id
        self.received_updates = updates

        if self.error is not None:
            raise self.error

        assert self.user is not None
        return self.user


class FakeChangeUserStatus:
    def __init__(self, user: User) -> None:
        self.user = user
        self.received_actor: User | None = None
        self.received_user_id: UUID | None = None
        self.received_is_active: bool | None = None

    def execute(
        self,
        *,
        actor: User,
        user_id: UUID,
        is_active: bool,
    ) -> User:
        self.received_actor = actor
        self.received_user_id = user_id
        self.received_is_active = is_active

        return self.user


class FakeChangeUserRole:
    def __init__(self, user: User) -> None:
        self.user = user
        self.received_actor: User | None = None
        self.received_user_id: UUID | None = None
        self.received_role_id: UUID | None = None

    def execute(
        self,
        *,
        actor: User,
        user_id: UUID,
        role_id: UUID,
    ) -> User:
        self.received_actor = actor
        self.received_user_id = user_id
        self.received_role_id = role_id

        return self.user


class FakeDeleteUser:
    def __init__(
        self,
        *,
        error: Exception | None = None,
    ) -> None:
        self.error = error
        self.received_actor: User | None = None
        self.received_user_id: UUID | None = None

    def execute(
        self,
        *,
        actor: User,
        user_id: UUID,
    ) -> None:
        self.received_actor = actor
        self.received_user_id = user_id

        if self.error is not None:
            raise self.error


def test_list_users_returns_paginated_response_and_forwards_query(
    client: TestClient,
) -> None:
    actor = make_admin()

    user = make_user()

    fake = FakeListUsers(
        Page(
            items=[user],
            page=2,
            page_size=10,
            total=11,
            total_pages=2,
            has_next=False,
            has_previous=True,
        )
    )

    app.dependency_overrides[get_current_user] = lambda: actor
    app.dependency_overrides[get_list_users] = lambda: fake

    response = client.get(
        "/api/users",
        params={
            "page": 2,
            "page_size": 10,
            "sort": "-email",
            "search": "alice",
            "role": "User",
            "is_active": "true",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert len(body["items"]) == 1
    assert body["items"][0]["id"] == str(user.id)
    assert body["items"][0]["email"] == "alice@example.com"

    assert body["pagination"] == {
        "page": 2,
        "page_size": 10,
        "total": 11,
        "total_pages": 2,
        "has_next": False,
        "has_previous": True,
    }

    assert fake.received is not None
    assert fake.received["page"] == 2
    assert fake.received["page_size"] == 10
    assert fake.received["search"] == "alice"
    assert fake.received["role"] == "User"
    assert fake.received["is_active"] is True

    sort_options = fake.received["sort_options"]

    assert sort_options.field == "email"
    assert sort_options.descending is True


def test_list_users_rejects_invalid_pagination(
    client: TestClient,
) -> None:
    actor = make_admin()

    app.dependency_overrides[get_current_user] = lambda: actor

    response = client.get(
        "/api/users",
        params={"page": 0},
    )

    assert response.status_code == 422

    assert any(error["field"] == "page" for error in response.json()["errors"])


def test_list_users_requires_user_read_permission(
    client: TestClient,
) -> None:
    actor = make_user(
        role_name="NoPermissions",
        role_level=50,
    )

    fake = FakeListUsers(
        Page(
            items=[],
            page=1,
            page_size=20,
            total=0,
            total_pages=0,
            has_next=False,
            has_previous=False,
        )
    )

    app.dependency_overrides[get_current_user] = lambda: actor
    app.dependency_overrides[get_list_users] = lambda: fake

    response = client.get("/api/users")

    assert response.status_code == 403
    assert response.json() == {"message": "Permission denied."}

    assert fake.received is None


def test_get_user_returns_user(
    client: TestClient,
) -> None:
    actor = make_admin()
    user = make_user()

    fake = FakeGetUser(user=user)

    app.dependency_overrides[get_current_user] = lambda: actor
    app.dependency_overrides[get_user_use_case] = lambda: fake

    response = client.get(f"/api/users/{user.id}")

    assert response.status_code == 200
    assert response.json()["id"] == str(user.id)
    assert response.json()["email"] == user.email

    assert fake.received_id == user.id


def test_get_user_maps_missing_user_to_not_found(
    client: TestClient,
) -> None:
    actor = make_admin()
    missing_id = uuid4()

    fake = FakeGetUser(
        error=UserNotFoundError(),
    )

    app.dependency_overrides[get_current_user] = lambda: actor
    app.dependency_overrides[get_user_use_case] = lambda: fake

    response = client.get(f"/api/users/{missing_id}")

    assert response.status_code == 404
    assert response.json() == {"message": "User not found!"}


def test_create_user_returns_created_user_and_forwards_payload(
    client: TestClient,
) -> None:
    actor = make_admin()
    role_id = uuid4()

    created_user = make_user(
        first_name="Bob",
        last_name="Smith",
        email="bob@example.com",
    )

    fake = FakeCreateUser(created_user)

    app.dependency_overrides[get_current_user] = lambda: actor
    app.dependency_overrides[get_create_user] = lambda: fake

    response = client.post(
        "/api/users",
        json={
            "first_name": "  Bob ",
            "last_name": " Smith  ",
            "email": "bob@example.com",
            "password": "password123",
            "role_id": str(role_id),
            "phone": "   ",
        },
    )

    assert response.status_code == 201

    body = response.json()

    assert body["id"] == str(created_user.id)
    assert body["email"] == "bob@example.com"

    assert fake.received == {
        "actor": actor,
        "first_name": "Bob",
        "last_name": "Smith",
        "email": "bob@example.com",
        "password": "password123",
        "role_id": role_id,
        "phone": None,
    }


def test_create_user_rejects_short_password(
    client: TestClient,
) -> None:
    actor = make_admin()

    app.dependency_overrides[get_current_user] = lambda: actor

    response = client.post(
        "/api/users",
        json={
            "first_name": "Bob",
            "last_name": "Smith",
            "email": "bob@example.com",
            "password": "short",
            "role_id": str(uuid4()),
        },
    )

    assert response.status_code == 422

    assert any(error["field"] == "password" for error in response.json()["errors"])


def test_update_user_forwards_only_provided_fields(
    client: TestClient,
) -> None:
    actor = make_admin()
    target = make_user()

    updated = make_user(
        first_name="Updated",
        email=target.email,
    )
    updated.id = target.id

    fake = FakeUpdateUser(user=updated)

    app.dependency_overrides[get_current_user] = lambda: actor
    app.dependency_overrides[get_update_user] = lambda: fake

    response = client.patch(
        f"/api/users/{target.id}",
        json={
            "first_name": "  Updated  ",
            "phone": "   ",
        },
    )

    assert response.status_code == 200

    assert response.json()["first_name"] == "Updated"

    assert fake.received_actor is actor
    assert fake.received_user_id == target.id
    assert fake.received_updates == {
        "first_name": "Updated",
        "phone": None,
    }


def test_update_user_rejects_empty_payload(
    client: TestClient,
) -> None:
    actor = make_admin()

    app.dependency_overrides[get_current_user] = lambda: actor

    response = client.patch(
        f"/api/users/{uuid4()}",
        json={},
    )

    assert response.status_code == 422

    assert any(
        error["message"] == "At least one field must be provided."
        for error in response.json()["errors"]
    )


def test_update_user_maps_authorization_error_to_forbidden(
    client: TestClient,
) -> None:
    actor = make_admin()
    target_id = uuid4()

    fake = FakeUpdateUser(
        error=AuthorizationError(AuthorizationReason.CANNOT_MANAGE_USER)
    )

    app.dependency_overrides[get_current_user] = lambda: actor
    app.dependency_overrides[get_update_user] = lambda: fake

    response = client.patch(
        f"/api/users/{target_id}",
        json={
            "first_name": "Updated",
        },
    )

    assert response.status_code == 403
    assert response.json() == {"message": "You are not authorized to manage this user."}


def test_change_user_status_returns_updated_user(
    client: TestClient,
) -> None:
    actor = make_admin()

    target = make_user(
        is_active=False,
    )

    fake = FakeChangeUserStatus(target)

    app.dependency_overrides[get_current_user] = lambda: actor
    app.dependency_overrides[get_change_status] = lambda: fake

    response = client.patch(
        f"/api/users/{target.id}/status",
        json={
            "is_active": False,
        },
    )

    assert response.status_code == 200
    assert response.json()["is_active"] is False

    assert fake.received_actor is actor
    assert fake.received_user_id == target.id
    assert fake.received_is_active is False


def test_change_user_role_forwards_role_id(
    client: TestClient,
) -> None:
    actor = make_admin()

    new_role_id = uuid4()

    target = make_user(
        role_name="Support",
        role_level=40,
    )

    fake = FakeChangeUserRole(target)

    app.dependency_overrides[get_current_user] = lambda: actor
    app.dependency_overrides[get_change_role] = lambda: fake

    response = client.patch(
        f"/api/users/{target.id}/role",
        json={
            "role_id": str(new_role_id),
        },
    )

    assert response.status_code == 200

    assert fake.received_actor is actor
    assert fake.received_user_id == target.id
    assert fake.received_role_id == new_role_id


def test_delete_user_returns_no_content(
    client: TestClient,
) -> None:
    actor = make_admin()
    target_id = uuid4()

    fake = FakeDeleteUser()

    app.dependency_overrides[get_current_user] = lambda: actor
    app.dependency_overrides[get_delete_user] = lambda: fake

    response = client.delete(f"/api/users/{target_id}")

    assert response.status_code == 204
    assert response.content == b""

    assert fake.received_actor is actor
    assert fake.received_user_id == target_id


def test_delete_user_maps_active_user_error_to_conflict(
    client: TestClient,
) -> None:
    actor = make_admin()
    target_id = uuid4()

    fake = FakeDeleteUser(
        error=ActiveUserDeletionError(),
    )

    app.dependency_overrides[get_current_user] = lambda: actor
    app.dependency_overrides[get_delete_user] = lambda: fake

    response = client.delete(f"/api/users/{target_id}")

    assert response.status_code == 409
    assert response.json() == {
        "message": ("Active users must be deactivated before they can be deleted.")
    }
