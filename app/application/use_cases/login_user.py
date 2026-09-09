from app.application.errors import InactiveUserError, InvalidCredentialsError
from app.application.ports.password_hasher import PasswordHasher
from app.application.ports.token_service import TokenService
from app.application.ports.unit_of_work import UnitOfWork


class LoginUser:
    def __init__(
        self,
        uow: UnitOfWork,
        password_hasher: PasswordHasher,
        token_service: TokenService,
    ) -> None:
        self.uow = uow
        self.password_hasher = password_hasher
        self.token_service = token_service

    def execute(self, email: str, password: str) -> str:
        with self.uow:
            user = self.uow.users.get_by_email(email)
            if user is None:
                raise InvalidCredentialsError()
            if not self.password_hasher.verify(password, user.password_hash):
                raise InvalidCredentialsError()
            if not user.is_active:
                raise InactiveUserError()
            access_token = self.token_service.create_access_token(user.id)
            return access_token
