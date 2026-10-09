from datetime import datetime, timezone

from app.application.errors import (
    InactiveUserError,
    InvalidAccessTokenError,
    InvalidCredentialsError,
)
from app.application.ports.password_hasher import PasswordHasher
from app.application.ports.token_service import TokenService
from app.application.ports.unit_of_work import UnitOfWork


class ReauthenticateUser:

    def __init__(
        self,
        uow: UnitOfWork,
        password_hasher: PasswordHasher,
        token_service: TokenService,
    ) -> None:
        self.uow = uow
        self.password_hasher = password_hasher
        self.token_service = token_service

    def execute(self, access_token: str, current_password: str) -> str:
        claims = self.token_service.decode_access_token(access_token)
        with self.uow:
            user = self.uow.users.get_by_id(claims.user_id)
            if user is None:
                raise InvalidAccessTokenError()
            if not user.is_active:
                raise InactiveUserError()
            session = self.uow.auth_sessions.get_by_id(claims.session_id)
            if session is None:
                raise InvalidAccessTokenError()
            if session.user_id != user.id:
                raise InvalidAccessTokenError()
            if session.expires_at <= datetime.now(timezone.utc):
                raise InvalidAccessTokenError()
            if session.revoked_at is not None:
                raise InvalidAccessTokenError()
            password_ok = self.password_hasher.verify(
                current_password, user.password_hash
            )
            if not password_ok:
                raise InvalidCredentialsError()
            session.authenticated_at = datetime.now(timezone.utc)
            self.uow.auth_sessions.update(session)
            access_token = self.token_service.create_access_token(
                user_id=user.id,
                session_id=session.id,
                authenticated_at=session.authenticated_at,
            )
            self.uow.commit()
            return access_token
