from app.application.use_cases.users.create_user import CreateUser
from app.application.use_cases.users.get_user import GetUser
from app.application.use_cases.users.list_users import ListUsers
from app.infrastructure.database.session import SessionFactory
from app.infrastructure.security.password_hasher import Argon2PasswordHasher
from app.infrastructure.uow.sqlalchemy import SqlAlchemyUnitOfWork


def get_user_use_case() -> GetUser:
    uow = SqlAlchemyUnitOfWork(SessionFactory)

    return GetUser(
        uow=uow,
    )


def get_list_users() -> ListUsers:
    uow = SqlAlchemyUnitOfWork(SessionFactory)
    return ListUsers(uow=uow)


def get_create_user() -> CreateUser:
    password_hasher = Argon2PasswordHasher()
    uow = SqlAlchemyUnitOfWork(SessionFactory)

    return CreateUser(
        uow=uow,
        password_hasher=password_hasher,
    )
