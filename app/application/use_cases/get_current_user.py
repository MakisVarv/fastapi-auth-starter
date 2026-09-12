from app.application.errors import InactiveUserError, InvalidAccessTokenError
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

    def execute(self, token: str) -> User:
        claims = self.token_service.decode_access_token(token)
        with self.uow:
            user = self.uow.users.get_by_id(claims.user_id)
            if user is None:
                raise InvalidAccessTokenError()
            if not user.is_active:
                raise InactiveUserError()
            return user
