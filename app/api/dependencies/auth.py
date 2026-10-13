from functools import cache
from typing import Callable

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.application.errors import InvalidAccessTokenError, PermissionDeniedError
from app.application.use_cases.auth.change_password import ChangePassword
from app.application.use_cases.auth.get_current_user import GetCurrentUser
from app.application.use_cases.auth.login_user import LoginUser
from app.application.use_cases.auth.logout_session import LogoutSession
from app.application.use_cases.auth.reauthenticate_user import ReauthenticateUser
from app.application.use_cases.auth.refresh_session import RefreshSession
from app.application.use_cases.auth.register_user import RegisterUser
from app.application.use_cases.auth.update_current_user import UpdateCurrentUser
from app.domain.entities.user import User
from app.infrastructure.database.session import SessionFactory
from app.infrastructure.security.password_hasher import Argon2PasswordHasher
from app.infrastructure.security.token_service import PyJWTTokenService
from app.infrastructure.uow.sqlalchemy import SqlAlchemyUnitOfWork

bearer_scheme = HTTPBearer(auto_error=False)


def get_register_user() -> RegisterUser:
    password_hasher = Argon2PasswordHasher()
    uow = SqlAlchemyUnitOfWork(SessionFactory)

    return RegisterUser(
        uow=uow,
        password_hasher=password_hasher,
    )


def get_login_user() -> LoginUser:
    password_hasher = Argon2PasswordHasher()
    uow = SqlAlchemyUnitOfWork(SessionFactory)
    token_service = PyJWTTokenService()

    return LoginUser(
        uow=uow, password_hasher=password_hasher, token_service=token_service
    )


def get_refresh_session() -> RefreshSession:
    uow = SqlAlchemyUnitOfWork(SessionFactory)
    token_service = PyJWTTokenService()
    return RefreshSession(uow=uow, token_service=token_service)


def get_current_user_use_case() -> GetCurrentUser:
    uow = SqlAlchemyUnitOfWork(SessionFactory)
    token_service = PyJWTTokenService()
    return GetCurrentUser(uow=uow, token_service=token_service)


def get_logout_session() -> LogoutSession:
    uow = SqlAlchemyUnitOfWork(SessionFactory)
    token_service = PyJWTTokenService()
    return LogoutSession(uow=uow, token_service=token_service)


def get_reauthenticate_user() -> ReauthenticateUser:
    password_hasher = Argon2PasswordHasher()
    uow = SqlAlchemyUnitOfWork(SessionFactory)
    token_service = PyJWTTokenService()
    return ReauthenticateUser(
        uow=uow, password_hasher=password_hasher, token_service=token_service
    )


def get_update_current_user() -> UpdateCurrentUser:
    uow = SqlAlchemyUnitOfWork(SessionFactory)
    return UpdateCurrentUser(uow=uow)


def get_change_password() -> ChangePassword:
    password_hasher = Argon2PasswordHasher()
    uow = SqlAlchemyUnitOfWork(SessionFactory)
    return ChangePassword(uow=uow, password_hasher=password_hasher)


@cache
def require_auth(*, fresh: bool = False) -> Callable[..., User]:
    def dependency(
        credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
        use_case: GetCurrentUser = Depends(get_current_user_use_case),
    ) -> User:
        if credentials is None:
            raise InvalidAccessTokenError()
        token = credentials.credentials
        user = use_case.execute(token=token, require_fresh=fresh)
        return user

    return dependency


def require_permission(permission_name: str) -> Callable[..., None]:

    def dependency(
        user: User = Depends(require_auth()),
    ) -> None:
        if not user.role.has_permission(permission_name):
            raise PermissionDeniedError()

    return dependency
