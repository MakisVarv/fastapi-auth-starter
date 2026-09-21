from app.application.use_cases.users.change_user_role import ChangeUserRole
from app.application.use_cases.users.change_user_status import ChangeUserStatus
from app.application.use_cases.users.create_user import CreateUser
from app.application.use_cases.users.delete_user import DeleteUser
from app.application.use_cases.users.get_user import GetUser
from app.application.use_cases.users.list_users import ListUsers
from app.application.use_cases.users.update_user import UpdateUser
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


def get_update_user() -> UpdateUser:
    uow = SqlAlchemyUnitOfWork(SessionFactory)

    return UpdateUser(
        uow=uow,
    )


def get_change_status() -> ChangeUserStatus:
    uow = SqlAlchemyUnitOfWork(SessionFactory)

    return ChangeUserStatus(
        uow=uow,
    )


def get_change_role() -> ChangeUserRole:
    uow = SqlAlchemyUnitOfWork(SessionFactory)

    return ChangeUserRole(
        uow=uow,
    )


def get_delete_user() -> DeleteUser:
    uow = SqlAlchemyUnitOfWork(SessionFactory)

    return DeleteUser(
        uow=uow,
    )
