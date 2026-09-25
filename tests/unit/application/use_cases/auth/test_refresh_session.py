from datetime import datetime, timedelta, timezone
from typing import cast
from uuid import UUID, uuid4

import pytest

from app.application.errors import (
    InactiveUserError,
    InvalidRefreshTokenError,
    RefreshTokenReplayError,
)
from app.application.ports.token_service import (
    IssuedRefreshToken,
    RefreshTokenClaims,
    TokenService,
)
from app.application.ports.unit_of_work import UnitOfWork
from app.application.use_cases.auth.refresh_session import RefreshSession
from app.domain.entities.auth_session import AuthSession
from app.domain.entities.role import Role
from app.domain.entities.user import User


class FakeUserRepository:
    def __init__(self, user: User | None) -> None:
        self.user = user
        self.requested_id: UUID | None = None

    def get_by_id(self, user_id: UUID) -> User | None:
        self.requested_id = user_id

        if self.user is not None and self.user.id == user_id:
            return self.user

        return None


class FakeAuthSessionRepository:
    def __init__(
        self,
        auth_session: AuthSession | None,
    ) -> None:
        self.auth_session = auth_session
        self.requested_id: UUID | None = None
        self.updated_session: AuthSession | None = None

    def get_by_id(
        self,
        session_id: UUID,
    ) -> AuthSession | None:
        self.requested_id = session_id

        if self.auth_session is not None and self.auth_session.id == session_id:
            return self.auth_session

        return None

    def update(self, auth_session: AuthSession) -> None:
        self.updated_session = auth_session


class FakeUnitOfWork:
    def __init__(
        self,
        *,
        user: User | None,
        auth_session: AuthSession | None,
    ) -> None:
        self.users = FakeUserRepository(user)
        self.auth_sessions = FakeAuthSessionRepository(auth_session)
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


class FakeTokenService:
    def __init__(
        self,
        *,
        claims: RefreshTokenClaims,
    ) -> None:
        self.claims = claims

        self.decoded_token: str | None = None
        self.access_token_user_id: UUID | None = None

        self.refresh_token_user_id: UUID | None = None
        self.refresh_token_session_id: UUID | None = None

        self.new_refresh_token = IssuedRefreshToken(
            token="new-refresh-token",
            jti="new-refresh-jti",
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )

    def decode_refresh_token(
        self,
        token: str,
    ) -> RefreshTokenClaims:
        self.decoded_token = token
        return self.claims

    def create_access_token(self, user_id: UUID) -> str:
        self.access_token_user_id = user_id
        return "new-access-token"

    def create_refresh_token(
        self,
        user_id: UUID,
        session_id: UUID,
    ) -> IssuedRefreshToken:
        self.refresh_token_user_id = user_id
        self.refresh_token_session_id = session_id

        return self.new_refresh_token

    def decode_access_token(self, token: str):
        raise NotImplementedError


def make_user(*, is_active: bool = True) -> User:
    return User(
        first_name="Test",
        last_name="User",
        email="user@example.com",
        password_hash="hashed-password",
        is_active=is_active,
        role=Role(
            name="User",
            level=10,
        ),
    )


def make_auth_session(
    *,
    user_id: UUID,
    session_id: UUID,
    jti: str = "current-jti",
    revoked_at: datetime | None = None,
    expires_at: datetime | None = None,
) -> AuthSession:
    return AuthSession(
        id=session_id,
        user_id=user_id,
        current_refresh_jti=jti,
        expires_at=expires_at or datetime.now(timezone.utc) + timedelta(days=1),
        revoked_at=revoked_at,
    )


def make_claims(
    *,
    user_id: UUID,
    session_id: UUID,
    jti: str = "current-jti",
) -> RefreshTokenClaims:
    return RefreshTokenClaims(
        user_id=user_id,
        session_id=session_id,
        jti=jti,
    )


def test_refresh_rotates_tokens_updates_session_and_commits() -> None:
    user = make_user()
    session_id = uuid4()

    auth_session = make_auth_session(
        user_id=user.id,
        session_id=session_id,
    )

    token_service = FakeTokenService(
        claims=make_claims(
            user_id=user.id,
            session_id=session_id,
        )
    )

    uow = FakeUnitOfWork(
        user=user,
        auth_session=auth_session,
    )

    use_case = RefreshSession(
        uow=cast(UnitOfWork, uow),
        token_service=cast(TokenService, token_service),
    )

    result = use_case.execute("old-refresh-token")

    assert result.access_token == "new-access-token"
    assert result.refresh_token == "new-refresh-token"

    assert token_service.decoded_token == "old-refresh-token"
    assert token_service.access_token_user_id == user.id
    assert token_service.refresh_token_user_id == user.id
    assert token_service.refresh_token_session_id == session_id

    assert auth_session.current_refresh_jti == "new-refresh-jti"
    assert auth_session.expires_at == token_service.new_refresh_token.expires_at

    assert uow.auth_sessions.updated_session is auth_session
    assert uow.committed is True


def test_refresh_rejects_missing_auth_session() -> None:
    user = make_user()
    session_id = uuid4()

    token_service = FakeTokenService(
        claims=make_claims(
            user_id=user.id,
            session_id=session_id,
        )
    )

    uow = FakeUnitOfWork(
        user=user,
        auth_session=None,
    )

    use_case = RefreshSession(
        uow=cast(UnitOfWork, uow),
        token_service=cast(TokenService, token_service),
    )

    with pytest.raises(InvalidRefreshTokenError):
        use_case.execute("refresh-token")

    assert uow.auth_sessions.updated_session is None
    assert uow.committed is False


def test_refresh_rejects_revoked_session() -> None:
    user = make_user()
    session_id = uuid4()

    auth_session = make_auth_session(
        user_id=user.id,
        session_id=session_id,
        revoked_at=datetime.now(timezone.utc),
    )

    token_service = FakeTokenService(
        claims=make_claims(
            user_id=user.id,
            session_id=session_id,
        )
    )

    uow = FakeUnitOfWork(
        user=user,
        auth_session=auth_session,
    )

    use_case = RefreshSession(
        uow=cast(UnitOfWork, uow),
        token_service=cast(TokenService, token_service),
    )

    with pytest.raises(InvalidRefreshTokenError):
        use_case.execute("refresh-token")

    assert uow.auth_sessions.updated_session is None
    assert uow.committed is False


def test_refresh_detects_replay_revokes_session_and_commits() -> None:
    user = make_user()
    session_id = uuid4()

    auth_session = make_auth_session(
        user_id=user.id,
        session_id=session_id,
        jti="current-jti",
    )

    token_service = FakeTokenService(
        claims=make_claims(
            user_id=user.id,
            session_id=session_id,
            jti="old-jti",
        )
    )

    uow = FakeUnitOfWork(
        user=user,
        auth_session=auth_session,
    )

    use_case = RefreshSession(
        uow=cast(UnitOfWork, uow),
        token_service=cast(TokenService, token_service),
    )

    with pytest.raises(RefreshTokenReplayError):
        use_case.execute("replayed-token")

    assert auth_session.revoked_at is not None
    assert uow.auth_sessions.updated_session is auth_session
    assert uow.committed is True

    assert token_service.access_token_user_id is None
    assert token_service.refresh_token_user_id is None


def test_refresh_rejects_user_mismatch() -> None:
    user = make_user()
    session_id = uuid4()

    auth_session = make_auth_session(
        user_id=user.id,
        session_id=session_id,
    )

    different_user_id = uuid4()

    token_service = FakeTokenService(
        claims=make_claims(
            user_id=different_user_id,
            session_id=session_id,
        )
    )

    uow = FakeUnitOfWork(
        user=user,
        auth_session=auth_session,
    )

    use_case = RefreshSession(
        uow=cast(UnitOfWork, uow),
        token_service=cast(TokenService, token_service),
    )

    with pytest.raises(InvalidRefreshTokenError):
        use_case.execute("refresh-token")

    assert uow.users.requested_id is None
    assert uow.auth_sessions.updated_session is None
    assert uow.committed is False


def test_refresh_rejects_missing_user() -> None:
    user = make_user()
    session_id = uuid4()

    auth_session = make_auth_session(
        user_id=user.id,
        session_id=session_id,
    )

    token_service = FakeTokenService(
        claims=make_claims(
            user_id=user.id,
            session_id=session_id,
        )
    )

    uow = FakeUnitOfWork(
        user=None,
        auth_session=auth_session,
    )

    use_case = RefreshSession(
        uow=cast(UnitOfWork, uow),
        token_service=cast(TokenService, token_service),
    )

    with pytest.raises(InvalidRefreshTokenError):
        use_case.execute("refresh-token")

    assert uow.auth_sessions.updated_session is None
    assert uow.committed is False


def test_refresh_inactive_user_revokes_session_and_commits() -> None:
    user = make_user(is_active=False)
    session_id = uuid4()

    auth_session = make_auth_session(
        user_id=user.id,
        session_id=session_id,
    )

    token_service = FakeTokenService(
        claims=make_claims(
            user_id=user.id,
            session_id=session_id,
        )
    )

    uow = FakeUnitOfWork(
        user=user,
        auth_session=auth_session,
    )

    use_case = RefreshSession(
        uow=cast(UnitOfWork, uow),
        token_service=cast(TokenService, token_service),
    )

    with pytest.raises(InactiveUserError):
        use_case.execute("refresh-token")

    assert auth_session.revoked_at is not None
    assert uow.auth_sessions.updated_session is auth_session
    assert uow.committed is True

    assert token_service.access_token_user_id is None
    assert token_service.refresh_token_user_id is None


def test_refresh_rejects_expired_session() -> None:
    user = make_user()
    session_id = uuid4()

    auth_session = make_auth_session(
        user_id=user.id,
        session_id=session_id,
        expires_at=datetime.now(timezone.utc) - timedelta(seconds=1),
    )

    token_service = FakeTokenService(
        claims=make_claims(
            user_id=user.id,
            session_id=session_id,
        )
    )

    uow = FakeUnitOfWork(
        user=user,
        auth_session=auth_session,
    )

    use_case = RefreshSession(
        uow=cast(UnitOfWork, uow),
        token_service=cast(TokenService, token_service),
    )

    with pytest.raises(InvalidRefreshTokenError):
        use_case.execute("refresh-token")

    assert uow.auth_sessions.updated_session is None
    assert uow.committed is False

    assert token_service.access_token_user_id is None
    assert token_service.refresh_token_user_id is None
