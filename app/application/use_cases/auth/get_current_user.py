from datetime import datetime, timezone

from app.application.common.authentication import is_authentication_fresh
from app.application.errors import (
    FreshAuthenticationRequiredError,
    InactiveUserError,
    InvalidAccessTokenError,
)
from app.application.ports.token_service import TokenService
from app.application.ports.unit_of_work import UnitOfWork
from app.domain.entities.user import User


class GetCurrentUser:
    def __init__(
        self,
        uow: UnitOfWork,
        token_service: TokenService,
    ) -> None:
        self.uow = uow
        self.token_service = token_service

    def execute(self, token: str, *, require_fresh: bool = False) -> User:
        claims = self.token_service.decode_access_token(token)
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
            if session.revoked_at is not None:
                raise InvalidAccessTokenError()
            if session.expires_at <= datetime.now(timezone.utc):
                raise InvalidAccessTokenError()
            if require_fresh and not (
                claims.is_fresh
                and is_authentication_fresh(
                    claims.authenticated_at,
                    datetime.now(timezone.utc),
                )
            ):
                raise FreshAuthenticationRequiredError()
            return user
