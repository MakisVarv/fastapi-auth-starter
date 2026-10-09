from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt
import pytest

from app.application.errors import (
    ExpiredAccessTokenError,
    InvalidAccessTokenError,
    InvalidRefreshTokenError,
)
from app.infrastructure.config import settings
from app.infrastructure.security.token_service import PyJWTTokenService


@pytest.fixture
def token_service() -> PyJWTTokenService:
    return PyJWTTokenService()


def encode(payload: dict) -> str:
    return jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def test_access_token_round_trip_preserves_authentication_context(
    token_service: PyJWTTokenService,
) -> None:
    user_id = uuid4()
    session_id = uuid4()
    authenticated_at = datetime.now(timezone.utc).replace(microsecond=0)

    token = token_service.create_access_token(
        user_id=user_id,
        session_id=session_id,
        authenticated_at=authenticated_at,
        is_fresh=True,
    )

    claims = token_service.decode_access_token(token)

    assert claims.user_id == user_id
    assert claims.session_id == session_id
    assert claims.authenticated_at == authenticated_at


def test_refresh_token_round_trip_preserves_session_identity(
    token_service: PyJWTTokenService,
) -> None:
    user_id = uuid4()
    session_id = uuid4()

    issued = token_service.create_refresh_token(
        user_id=user_id,
        session_id=session_id,
    )

    claims = token_service.decode_refresh_token(issued.token)

    assert claims.user_id == user_id
    assert claims.session_id == session_id
    assert claims.jti == issued.jti


def test_expired_access_token_maps_to_expired_access_token_error(
    token_service: PyJWTTokenService,
) -> None:
    token = encode(
        {
            "sub": str(uuid4()),
            "type": "access",
            "exp": datetime.now(timezone.utc) - timedelta(seconds=1),
        }
    )

    with pytest.raises(ExpiredAccessTokenError):
        token_service.decode_access_token(token)


def test_tampered_access_token_maps_to_invalid_access_token_error(
    token_service: PyJWTTokenService,
) -> None:
    wrong_secret = "wrong-secret-key-that-is-at-least-32-bytes"
    token = jwt.encode(
        {
            "sub": str(uuid4()),
            "type": "access",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
        },
        wrong_secret,
        algorithm=settings.JWT_ALGORITHM,
    )

    with pytest.raises(InvalidAccessTokenError):
        token_service.decode_access_token(token)


def test_refresh_token_cannot_be_used_as_access_token(
    token_service: PyJWTTokenService,
) -> None:
    issued = token_service.create_refresh_token(
        user_id=uuid4(),
        session_id=uuid4(),
    )

    with pytest.raises(InvalidAccessTokenError):
        token_service.decode_access_token(issued.token)


def test_access_token_cannot_be_used_as_refresh_token(
    token_service: PyJWTTokenService,
) -> None:
    token = token_service.create_access_token(
        user_id=uuid4(),
        session_id=uuid4(),
        authenticated_at=datetime.now(timezone.utc),
        is_fresh=False,
    )

    with pytest.raises(InvalidRefreshTokenError):
        token_service.decode_refresh_token(token)


@pytest.mark.parametrize(
    "payload",
    [
        {
            "type": "access",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
        },
        {
            "sub": "not-a-uuid",
            "type": "access",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
        },
    ],
)
def test_malformed_access_claims_map_to_invalid_access_token_error(
    token_service: PyJWTTokenService,
    payload: dict,
) -> None:
    token = encode(payload)

    with pytest.raises(InvalidAccessTokenError):
        token_service.decode_access_token(token)


@pytest.mark.parametrize(
    "payload",
    [
        {
            "sub": str(uuid4()),
            "sid": str(uuid4()),
            "type": "refresh",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
        },
        {
            "sub": "not-a-uuid",
            "sid": str(uuid4()),
            "jti": "jti",
            "type": "refresh",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
        },
        {
            "sub": str(uuid4()),
            "sid": "not-a-uuid",
            "jti": "jti",
            "type": "refresh",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
        },
    ],
)
def test_malformed_refresh_claims_map_to_invalid_refresh_token_error(
    token_service: PyJWTTokenService,
    payload: dict,
) -> None:
    token = encode(payload)

    with pytest.raises(InvalidRefreshTokenError):
        token_service.decode_refresh_token(token)


def test_expired_refresh_token_maps_to_invalid_refresh_token_error(
    token_service: PyJWTTokenService,
) -> None:
    token = encode(
        {
            "sub": str(uuid4()),
            "sid": str(uuid4()),
            "jti": "jti",
            "type": "refresh",
            "exp": datetime.now(timezone.utc) - timedelta(seconds=1),
        }
    )

    with pytest.raises(InvalidRefreshTokenError):
        token_service.decode_refresh_token(token)
