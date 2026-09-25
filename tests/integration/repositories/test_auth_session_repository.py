from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.application.errors import AuthSessionNotFoundError
from app.domain.entities.auth_session import AuthSession
from app.domain.entities.role import Role
from app.domain.entities.user import User
from app.infrastructure.repositories.auth_session_repository import (
    SqlAlchemyAuthSessionRepository,
)
from app.infrastructure.repositories.role_repository import SqlAlchemyRoleRepository
from app.infrastructure.repositories.user_repository import SqlAlchemyUserRepository


def make_user(
    *,
    role: Role,
    email: str,
) -> User:
    return User(
        first_name="Test",
        last_name="User",
        email=email,
        password_hash="test-password-hash",
        role=role,
    )


def make_auth_session(
    *,
    user_id,
    current_refresh_jti: str = "refresh-jti-1",
) -> AuthSession:
    return AuthSession(
        user_id=user_id,
        current_refresh_jti=current_refresh_jti,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )


def test_add_and_get_by_id_persists_auth_session(
    db_session: Session,
) -> None:
    user_repository = SqlAlchemyUserRepository(db_session)
    role_repository = SqlAlchemyRoleRepository(db_session)
    auth_session_repository = SqlAlchemyAuthSessionRepository(db_session)

    user_role = role_repository.get_by_name("User")
    assert user_role is not None

    user = make_user(
        role=user_role,
        email="auth-session-user@example.com",
    )

    user_repository.add(user)
    db_session.commit()

    auth_session = make_auth_session(user_id=user.id)

    auth_session_repository.add(auth_session)
    db_session.commit()
    db_session.expire_all()

    persisted_session = auth_session_repository.get_by_id(auth_session.id)

    assert persisted_session is not None
    assert persisted_session.id == auth_session.id
    assert persisted_session.user_id == user.id
    assert persisted_session.current_refresh_jti == "refresh-jti-1"
    assert persisted_session.expires_at == auth_session.expires_at
    assert persisted_session.revoked_at is None


def test_update_persists_rotated_and_revoked_session_state(
    db_session: Session,
) -> None:
    user_repository = SqlAlchemyUserRepository(db_session)
    role_repository = SqlAlchemyRoleRepository(db_session)
    auth_session_repository = SqlAlchemyAuthSessionRepository(db_session)

    user_role = role_repository.get_by_name("User")
    assert user_role is not None

    user = make_user(
        role=user_role,
        email="auth-session-update@example.com",
    )

    user_repository.add(user)
    db_session.commit()

    auth_session = make_auth_session(user_id=user.id)

    auth_session_repository.add(auth_session)
    db_session.commit()

    new_expiration = datetime.now(timezone.utc) + timedelta(days=14)
    revoked_at = datetime.now(timezone.utc)

    auth_session.current_refresh_jti = "refresh-jti-2"
    auth_session.expires_at = new_expiration
    auth_session.revoked_at = revoked_at

    auth_session_repository.update(auth_session)
    db_session.commit()
    db_session.expire_all()

    persisted_session = auth_session_repository.get_by_id(auth_session.id)

    assert persisted_session is not None
    assert persisted_session.current_refresh_jti == "refresh-jti-2"
    assert persisted_session.expires_at == new_expiration
    assert persisted_session.revoked_at == revoked_at


def test_update_missing_auth_session_raises_not_found(
    db_session: Session,
) -> None:
    repository = SqlAlchemyAuthSessionRepository(db_session)

    missing_session = AuthSession(
        id=uuid4(),
        user_id=uuid4(),
        current_refresh_jti="missing-jti",
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )

    with pytest.raises(AuthSessionNotFoundError):
        repository.update(missing_session)


def test_deleting_user_cascades_auth_sessions(
    db_session: Session,
) -> None:
    user_repository = SqlAlchemyUserRepository(db_session)
    role_repository = SqlAlchemyRoleRepository(db_session)
    auth_session_repository = SqlAlchemyAuthSessionRepository(db_session)

    user_role = role_repository.get_by_name("User")
    assert user_role is not None

    user = make_user(
        role=user_role,
        email="cascade-user@example.com",
    )

    user_repository.add(user)
    db_session.commit()

    auth_session = make_auth_session(user_id=user.id)

    auth_session_repository.add(auth_session)
    db_session.commit()

    assert auth_session_repository.get_by_id(auth_session.id) is not None

    user_repository.delete(user)
    db_session.commit()
    db_session.expire_all()

    assert auth_session_repository.get_by_id(auth_session.id) is None
