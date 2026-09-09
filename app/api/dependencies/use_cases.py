from app.application.use_cases.login_user import LoginUser
from app.application.use_cases.register_user import RegisterUser
from app.infrastructure.database.session import SessionFactory
from app.infrastructure.security.password_hasher import Argon2PasswordHasher
from app.infrastructure.security.token_service import PyJWTTokenService
from app.infrastructure.uow.sqlalchemy import SqlAlchemyUnitOfWork


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
