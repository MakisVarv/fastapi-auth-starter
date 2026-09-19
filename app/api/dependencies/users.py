from app.application.use_cases.users.get_user import GetUser
from app.application.use_cases.users.list_users import ListUsers
from app.infrastructure.database.session import SessionFactory
from app.infrastructure.uow.sqlalchemy import SqlAlchemyUnitOfWork


def get_user_use_case() -> GetUser:
    uow = SqlAlchemyUnitOfWork(SessionFactory)

    return GetUser(
        uow=uow,
    )


def get_list_users() -> ListUsers:
    uow = SqlAlchemyUnitOfWork(SessionFactory)
    return ListUsers(uow=uow)
