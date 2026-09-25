from typing import Any

from fastapi.testclient import TestClient

from app.api.dependencies.auth import (
    get_current_user_use_case,
    get_login_user,
    get_logout_session,
    get_refresh_session,
    get_register_user,
    get_update_current_user,
)
from app.application.errors import (
    EmailAlreadyRegisteredError,
    InvalidAccessTokenError,
    InvalidCredentialsError,
    InvalidRefreshTokenError,
    RefreshTokenReplayError,
)
from app.application.use_cases.auth.login_user import LoginResult
from app.application.use_cases.auth.refresh_session import RefreshResult
from app.domain.entities.role import Role
from app.domain.entities.user import User
from app.main import app


def make_user(
    *,
    first_name: str = "Alice",
    last_name: str = "Stone",
    email: str = "alice@example.com",
    phone: str | None = None,
    is_active: bool = True,
) -> User:
    return User(
        first_name=first_name,
        last_name=last_name,
        email=email,
        phone=phone,
        password_hash="hashed-password",
        is_active=is_active,
        role=Role(
            name="User",
            level=10,
        ),
    )


class FakeRegisterUser:
    def __init__(
        self,
        *,
        user: User | None = None,
        error: Exception | None = None,
    ) -> None:
        self.user = user
        self.error = error
        self.received: dict[str, Any] | None = None

    def execute(
        self,
        *,
        first_name: str,
        last_name: str,
        email: str,
        password: str,
        phone: str | None = None,
    ) -> User:
        self.received = {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "password": password,
            "phone": phone,
        }

        if self.error is not None:
            raise self.error

        assert self.user is not None
        return self.user


class FakeLoginUser:
    def __init__(
        self,
        *,
        result: LoginResult | None = None,
        error: Exception | None = None,
    ) -> None:
        self.result = result
        self.error = error
        self.received: dict[str, str] | None = None

    def execute(
        self,
        *,
        email: str,
        password: str,
    ) -> LoginResult:
        self.received = {
            "email": email,
            "password": password,
        }

        if self.error is not None:
            raise self.error

        assert self.result is not None
        return self.result


class FakeRefreshSession:
    def __init__(
        self,
        *,
        result: RefreshResult | None = None,
        error: Exception | None = None,
    ) -> None:
        self.result = result
        self.error = error
        self.received_token: str | None = None

    def execute(
        self,
        *,
        refresh_token: str,
    ) -> RefreshResult:
        self.received_token = refresh_token

        if self.error is not None:
            raise self.error

        assert self.result is not None
        return self.result


class FakeLogoutSession:
    def __init__(
        self,
        *,
        error: Exception | None = None,
    ) -> None:
        self.error = error
        self.received_token: str | None = None
        self.called = False

    def execute(
        self,
        *,
        refresh_token: str,
    ) -> None:
        self.called = True
        self.received_token = refresh_token

        if self.error is not None:
            raise self.error


class FakeGetCurrentUser:
    def __init__(
        self,
        *,
        user: User | None = None,
        error: Exception | None = None,
    ) -> None:
        self.user = user
        self.error = error
        self.received_token: str | None = None

    def execute(self, token: str) -> User:
        self.received_token = token

        if self.error is not None:
            raise self.error

        assert self.user is not None
        return self.user


class FakeUpdateCurrentUser:
    def __init__(self, user: User) -> None:
        self.user = user
        self.received_user_id = None
        self.received_updates: dict[str, str | None] | None = None

    def execute(
        self,
        *,
        user_id,
        updates: dict[str, str | None],
    ) -> User:
        self.received_user_id = user_id
        self.received_updates = updates
        return self.user


def test_register_returns_created_user(
    client: TestClient,
) -> None:
    user = make_user(
        first_name="Alice",
        last_name="Stone",
        phone=None,
    )

    fake = FakeRegisterUser(user=user)

    app.dependency_overrides[get_register_user] = lambda: fake

    response = client.post(
        "/api/auth/register",
        json={
            "first_name": "  Alice  ",
            "last_name": "  Stone ",
            "email": "alice@example.com",
            "password": "password123",
            "phone": "   ",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["id"] == str(user.id)
    assert body["first_name"] == "Alice"
    assert body["last_name"] == "Stone"
    assert body["email"] == "alice@example.com"
    assert body["phone"] is None
    assert body["is_active"] is True
    assert body["role"]["name"] == "User"

    assert "password_hash" not in body

    assert fake.received == {
        "first_name": "Alice",
        "last_name": "Stone",
        "email": "alice@example.com",
        "password": "password123",
        "phone": None,
    }


def test_register_returns_validation_error_for_empty_name(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/auth/register",
        json={
            "first_name": "   ",
            "last_name": "Stone",
            "email": "alice@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 422

    assert {
        "field": "first_name",
        "message": "Field cannot be empty.",
    } in response.json()["errors"]


def test_register_maps_duplicate_email_to_conflict(
    client: TestClient,
) -> None:
    fake = FakeRegisterUser(
        error=EmailAlreadyRegisteredError(),
    )

    app.dependency_overrides[get_register_user] = lambda: fake

    response = client.post(
        "/api/auth/register",
        json={
            "first_name": "Alice",
            "last_name": "Stone",
            "email": "alice@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 409
    assert response.json() == {"message": "Email is already registered."}


def test_login_returns_access_token_user_and_refresh_cookie(
    client: TestClient,
) -> None:
    user = make_user()

    fake = FakeLoginUser(
        result=LoginResult(
            access_token="access-token",
            refresh_token="refresh-token",
            user=user,
        )
    )

    app.dependency_overrides[get_login_user] = lambda: fake

    response = client.post(
        "/api/auth/login",
        json={
            "email": "alice@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["access_token"] == "access-token"
    assert body["token_type"] == "bearer"

    assert body["user"]["id"] == str(user.id)
    assert body["user"]["email"] == "alice@example.com"

    assert fake.received == {
        "email": "alice@example.com",
        "password": "password123",
    }

    set_cookie = response.headers["set-cookie"]

    assert "refresh_token=refresh-token" in set_cookie
    assert "HttpOnly" in set_cookie
    assert "SameSite=lax" in set_cookie


def test_login_maps_invalid_credentials_to_unauthorized(
    client: TestClient,
) -> None:
    fake = FakeLoginUser(
        error=InvalidCredentialsError(),
    )

    app.dependency_overrides[get_login_user] = lambda: fake

    response = client.post(
        "/api/auth/login",
        json={
            "email": "alice@example.com",
            "password": "wrong-password",
        },
    )

    assert response.status_code == 401
    assert response.json() == {"message": "Invalid credentials."}


def test_refresh_requires_refresh_cookie(
    client: TestClient,
) -> None:
    fake = FakeRefreshSession()

    app.dependency_overrides[get_refresh_session] = lambda: fake

    response = client.post("/api/auth/refresh")

    assert response.status_code == 401
    assert response.json() == {"message": "Invalid refresh token."}

    assert fake.received_token is None


def test_refresh_returns_access_token_and_rotates_cookie(
    client: TestClient,
) -> None:
    fake = FakeRefreshSession(
        result=RefreshResult(
            access_token="new-access-token",
            refresh_token="new-refresh-token",
        )
    )

    app.dependency_overrides[get_refresh_session] = lambda: fake

    client.cookies.set(
        "refresh_token",
        "old-refresh-token",
    )

    response = client.post("/api/auth/refresh")

    assert response.status_code == 200

    assert response.json() == {
        "access_token": "new-access-token",
        "token_type": "bearer",
    }

    assert fake.received_token == "old-refresh-token"

    set_cookie = response.headers["set-cookie"]

    assert "refresh_token=new-refresh-token" in set_cookie
    assert "HttpOnly" in set_cookie
    assert "SameSite=lax" in set_cookie


def test_refresh_maps_replay_to_unauthorized(
    client: TestClient,
) -> None:
    fake = FakeRefreshSession(
        error=RefreshTokenReplayError(),
    )

    app.dependency_overrides[get_refresh_session] = lambda: fake

    client.cookies.set(
        "refresh_token",
        "replayed-token",
    )

    response = client.post("/api/auth/refresh")

    assert response.status_code == 401
    assert response.json() == {"message": "Invalid refresh token."}


def test_logout_without_cookie_is_successful(
    client: TestClient,
) -> None:
    fake = FakeLogoutSession()

    app.dependency_overrides[get_logout_session] = lambda: fake

    response = client.post("/api/auth/logout")

    assert response.status_code == 200
    assert response.json() == {"message": "Logged out successfully."}

    assert fake.called is False

    set_cookie = response.headers["set-cookie"].lower()

    assert "refresh_token=" in set_cookie
    assert "max-age=0" in set_cookie


def test_logout_with_invalid_cookie_is_still_successful(
    client: TestClient,
) -> None:
    fake = FakeLogoutSession(
        error=InvalidRefreshTokenError(),
    )

    app.dependency_overrides[get_logout_session] = lambda: fake

    client.cookies.set(
        "refresh_token",
        "invalid-refresh-token",
    )

    response = client.post("/api/auth/logout")

    assert response.status_code == 200
    assert response.json() == {"message": "Logged out successfully."}

    assert fake.called is True
    assert fake.received_token == "invalid-refresh-token"

    assert "max-age=0" in response.headers["set-cookie"].lower()


def test_me_uses_bearer_token_and_returns_current_user(
    client: TestClient,
) -> None:
    user = make_user()

    fake = FakeGetCurrentUser(user=user)

    app.dependency_overrides[get_current_user_use_case] = lambda: fake

    response = client.get(
        "/api/auth/me",
        headers={
            "Authorization": "Bearer access-token",
        },
    )

    assert response.status_code == 200

    assert response.json()["id"] == str(user.id)
    assert response.json()["email"] == "alice@example.com"

    assert fake.received_token == "access-token"


def test_me_requires_bearer_token(
    client: TestClient,
) -> None:
    response = client.get("/api/auth/me")

    assert response.status_code == 401
    assert response.json() == {"message": "Invalid access token."}


def test_me_maps_invalid_access_token_to_unauthorized(
    client: TestClient,
) -> None:
    fake = FakeGetCurrentUser(
        error=InvalidAccessTokenError(),
    )

    app.dependency_overrides[get_current_user_use_case] = lambda: fake

    response = client.get(
        "/api/auth/me",
        headers={
            "Authorization": "Bearer invalid-token",
        },
    )

    assert response.status_code == 401
    assert response.json() == {"message": "Invalid access token."}

    assert fake.received_token == "invalid-token"


def test_update_me_forwards_only_provided_normalized_fields(
    client: TestClient,
) -> None:
    current_user = make_user()

    updated_user = make_user(
        first_name="Updated",
        last_name="Stone",
        phone=None,
    )
    updated_user.id = current_user.id

    current_user_use_case = FakeGetCurrentUser(
        user=current_user,
    )
    update_use_case = FakeUpdateCurrentUser(
        user=updated_user,
    )

    app.dependency_overrides[get_current_user_use_case] = lambda: current_user_use_case
    app.dependency_overrides[get_update_current_user] = lambda: update_use_case

    response = client.patch(
        "/api/auth/me",
        headers={
            "Authorization": "Bearer access-token",
        },
        json={
            "first_name": "  Updated  ",
            "phone": "   ",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["id"] == str(current_user.id)
    assert body["first_name"] == "Updated"
    assert body["phone"] is None

    assert update_use_case.received_user_id == current_user.id
    assert update_use_case.received_updates == {
        "first_name": "Updated",
        "phone": None,
    }


def test_update_me_rejects_empty_payload(
    client: TestClient,
) -> None:
    user = make_user()

    fake = FakeGetCurrentUser(user=user)

    app.dependency_overrides[get_current_user_use_case] = lambda: fake

    response = client.patch(
        "/api/auth/me",
        headers={
            "Authorization": "Bearer access-token",
        },
        json={},
    )

    assert response.status_code == 422

    assert any(
        error["message"] == "At least one field must be provided."
        for error in response.json()["errors"]
    )


def test_update_me_rejects_null_name(
    client: TestClient,
) -> None:
    user = make_user()

    fake = FakeGetCurrentUser(user=user)

    app.dependency_overrides[get_current_user_use_case] = lambda: fake

    response = client.patch(
        "/api/auth/me",
        headers={
            "Authorization": "Bearer access-token",
        },
        json={
            "first_name": None,
        },
    )

    assert response.status_code == 422

    assert {
        "field": "first_name",
        "message": "Field cannot be null.",
    } in response.json()["errors"]
