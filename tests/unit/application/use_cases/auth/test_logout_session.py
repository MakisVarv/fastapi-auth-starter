from datetime import datetime, timedelta, timezone
from typing import cast
from uuid import UUID, uuid4

import pytest

from app.application.errors import InvalidRefreshTokenError
from app.application.ports.token_service import (
    RefreshTokenClaims,
    TokenService,
)
from app.application.ports.unit_of_work import UnitOfWork
from app.application.use_cases.auth.logout_session import LogoutSession
from app.domain.entities.auth_session import AuthSession


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
        auth_session: AuthSession | None,
    ) -> None:
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
        claims: RefreshTokenClaims,
    ) -> None:
        self.claims = claims
        self.decoded_token: str | None = None

    def decode_refresh_token(
        self,
        token: str,
    ) -> RefreshTokenClaims:
        self.decoded_token = token
        return self.claims

    def create_access_token(self, user_id: UUID) -> str:
        raise NotImplementedError

    def create_refresh_token(self, user_id: UUID, session_id: UUID):
        raise NotImplementedError

    def decode_access_token(self, token: str):
        raise NotImplementedError


def make_auth_session(
    *,
    user_id: UUID,
    session_id: UUID,
    jti: str = "current-jti",
    revoked_at: datetime | None = None,
) -> AuthSession:
    return AuthSession(
        id=session_id,
        user_id=user_id,
        current_refresh_jti=jti,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        revoked_at=revoked_at,
    )


def test_logout_revokes_session_and_commits() -> None:
    user_id = uuid4()
    session_id = uuid4()

    auth_session = make_auth_session(
        user_id=user_id,
        session_id=session_id,
    )

    claims = RefreshTokenClaims(
        user_id=user_id,
        session_id=session_id,
        jti="current-jti",
    )

    uow = FakeUnitOfWork(auth_session)
    token_service = FakeTokenService(claims)

    use_case = LogoutSession(
        uow=cast(UnitOfWork, uow),
        token_service=cast(TokenService, token_service),
    )

    use_case.execute("refresh-token")

    assert token_service.decoded_token == "refresh-token"
    assert auth_session.revoked_at is not None
    assert uow.auth_sessions.updated_session is auth_session
    assert uow.committed is True


def test_logout_rejects_missing_session() -> None:
    user_id = uuid4()
    session_id = uuid4()

    claims = RefreshTokenClaims(
        user_id=user_id,
        session_id=session_id,
        jti="current-jti",
    )

    uow = FakeUnitOfWork(None)
    token_service = FakeTokenService(claims)

    use_case = LogoutSession(
        uow=cast(UnitOfWork, uow),
        token_service=cast(TokenService, token_service),
    )

    with pytest.raises(InvalidRefreshTokenError):
        use_case.execute("refresh-token")

    assert uow.auth_sessions.updated_session is None
    assert uow.committed is False


def test_logout_rejects_user_mismatch() -> None:
    user_id = uuid4()
    session_id = uuid4()

    auth_session = make_auth_session(
        user_id=user_id,
        session_id=session_id,
    )

    claims = RefreshTokenClaims(
        user_id=uuid4(),
        session_id=session_id,
        jti="current-jti",
    )

    uow = FakeUnitOfWork(auth_session)
    token_service = FakeTokenService(claims)

    use_case = LogoutSession(
        uow=cast(UnitOfWork, uow),
        token_service=cast(TokenService, token_service),
    )

    with pytest.raises(InvalidRefreshTokenError):
        use_case.execute("refresh-token")

    assert auth_session.revoked_at is None
    assert uow.auth_sessions.updated_session is None
    assert uow.committed is False


def test_logout_rejects_refresh_jti_mismatch() -> None:
    user_id = uuid4()
    session_id = uuid4()

    auth_session = make_auth_session(
        user_id=user_id,
        session_id=session_id,
        jti="current-jti",
    )

    claims = RefreshTokenClaims(
        user_id=user_id,
        session_id=session_id,
        jti="old-jti",
    )

    uow = FakeUnitOfWork(auth_session)
    token_service = FakeTokenService(claims)

    use_case = LogoutSession(
        uow=cast(UnitOfWork, uow),
        token_service=cast(TokenService, token_service),
    )

    with pytest.raises(InvalidRefreshTokenError):
        use_case.execute("refresh-token")

    assert auth_session.revoked_at is None
    assert uow.auth_sessions.updated_session is None
    assert uow.committed is False


def test_logout_rejects_already_revoked_session() -> None:
    user_id = uuid4()
    session_id = uuid4()

    revoked_at = datetime.now(timezone.utc)

    auth_session = make_auth_session(
        user_id=user_id,
        session_id=session_id,
        revoked_at=revoked_at,
    )

    claims = RefreshTokenClaims(
        user_id=user_id,
        session_id=session_id,
        jti="current-jti",
    )

    uow = FakeUnitOfWork(auth_session)
    token_service = FakeTokenService(claims)

    use_case = LogoutSession(
        uow=cast(UnitOfWork, uow),
        token_service=cast(TokenService, token_service),
    )

    with pytest.raises(InvalidRefreshTokenError):
        use_case.execute("refresh-token")

    assert auth_session.revoked_at == revoked_at
    assert uow.auth_sessions.updated_session is None
    assert uow.committed is False
