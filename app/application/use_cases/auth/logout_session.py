from datetime import datetime, timezone

from app.application.errors import InvalidRefreshTokenError
from app.application.ports.token_service import TokenService
from app.application.ports.unit_of_work import UnitOfWork


class LogoutSession:

    def __init__(self, uow: UnitOfWork, token_service: TokenService) -> None:
        self.uow = uow
        self.token_service = token_service

    def execute(self, refresh_token: str):
        claims = self.token_service.decode_refresh_token(refresh_token)
        with self.uow:
            auth_session = self.uow.auth_sessions.get_by_id(claims.session_id)
            if auth_session is None:
                raise InvalidRefreshTokenError()
            if auth_session.user_id != claims.user_id:
                raise InvalidRefreshTokenError()
            if auth_session.current_refresh_jti != claims.jti:
                raise InvalidRefreshTokenError()
            if auth_session.revoked_at is not None:
                raise InvalidRefreshTokenError()
            auth_session.revoked_at = datetime.now(timezone.utc)
            self.uow.auth_sessions.update(auth_session)
            self.uow.commit()
