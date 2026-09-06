from app.application.use_cases.register_user import RegisterUser
from app.infrastructure.database.session import SessionFactory
from app.infrastructure.security.password_hasher import Argon2PasswordHasher
from app.infrastructure.uow.sqlalchemy import SqlAlchemyUnitOfWork


def get_register_user() -> RegisterUser:
    password_hasher = Argon2PasswordHasher()
    uow = SqlAlchemyUnitOfWork(SessionFactory)

    return RegisterUser(
        uow=uow,
        password_hasher=password_hasher,
    )
