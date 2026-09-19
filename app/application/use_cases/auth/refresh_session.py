from dataclasses import dataclass
from datetime import datetime, timezone

from app.application.errors import (
    InactiveUserError,
    InvalidRefreshTokenError,
    RefreshTokenReplayError,
)
from app.application.ports.token_service import TokenService
from app.application.ports.unit_of_work import UnitOfWork


@dataclass(frozen=True)
class RefreshResult:
    access_token: str
    refresh_token: str


class RefreshSession:
    def __init__(
        self,
        uow: UnitOfWork,
        token_service: TokenService,
    ) -> None:
        self.uow = uow
        self.token_service = token_service

    def execute(self, refresh_token: str) -> RefreshResult:
        claims = self.token_service.decode_refresh_token(refresh_token)
        with self.uow:
            auth_session = self.uow.auth_sessions.get_by_id(claims.session_id)
            if auth_session is None:
                raise InvalidRefreshTokenError()
            if auth_session.revoked_at is not None:
                raise InvalidRefreshTokenError()
            if claims.jti != auth_session.current_refresh_jti:
                auth_session.revoked_at = datetime.now(timezone.utc)

                self.uow.auth_sessions.update(auth_session)
                self.uow.commit()

                raise RefreshTokenReplayError()
            if claims.user_id != auth_session.user_id:
                raise InvalidRefreshTokenError()
            user = self.uow.users.get_by_id(claims.user_id)
            if user is None:
                raise InvalidRefreshTokenError()
            if not user.is_active:
                auth_session.revoked_at = datetime.now(timezone.utc)

                self.uow.auth_sessions.update(auth_session)
                self.uow.commit()

                raise InactiveUserError()
            now = datetime.now(timezone.utc)

            if auth_session.expires_at <= now:
                raise InvalidRefreshTokenError()
            new_access_token = self.token_service.create_access_token(user.id)

            new_refresh_token = self.token_service.create_refresh_token(
                user_id=user.id,
                session_id=auth_session.id,
            )
            auth_session.current_refresh_jti = new_refresh_token.jti
            auth_session.expires_at = new_refresh_token.expires_at
            self.uow.auth_sessions.update(auth_session)
            self.uow.commit()
            return RefreshResult(
                access_token=new_access_token,
                refresh_token=new_refresh_token.token,
            )
