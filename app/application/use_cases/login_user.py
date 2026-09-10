from dataclasses import dataclass
from uuid import uuid4

from app.application.errors import InactiveUserError, InvalidCredentialsError
from app.application.ports.password_hasher import PasswordHasher
from app.application.ports.token_service import TokenService
from app.application.ports.unit_of_work import UnitOfWork
from app.domain.entities.auth_session import AuthSession


@dataclass(frozen=True)
class LoginResult:
    access_token: str
    refresh_token: str


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

    def execute(self, email: str, password: str) -> LoginResult:
        with self.uow:
            user = self.uow.users.get_by_email(email)
            if user is None:
                raise InvalidCredentialsError()
            if not self.password_hasher.verify(password, user.password_hash):
                raise InvalidCredentialsError()
            if not user.is_active:
                raise InactiveUserError()
            session_id = uuid4()
            access_token = self.token_service.create_access_token(user.id)
            refresh_token = self.token_service.create_refresh_token(
                user_id=user.id,
                session_id=session_id,
            )
            auth_session = AuthSession(
                id=session_id,
                user_id=user.id,
                current_refresh_jti=refresh_token.jti,
                expires_at=refresh_token.expires_at,
            )
            self.uow.auth_sessions.add(auth_session)
            self.uow.commit()
            return LoginResult(
                access_token=access_token,
                refresh_token=refresh_token.token,
            )
