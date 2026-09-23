from app.application.use_cases.roles.create_role import CreateRole
from app.application.use_cases.roles.get_role import GetRole
from app.application.use_cases.roles.list_roles import ListRoles
from app.infrastructure.database.session import SessionFactory
from app.infrastructure.uow.sqlalchemy import SqlAlchemyUnitOfWork


def get_list_roles() -> ListRoles:
    uow = SqlAlchemyUnitOfWork(SessionFactory)
    return ListRoles(uow=uow)


def get_role_use_case() -> GetRole:
    uow = SqlAlchemyUnitOfWork(SessionFactory)
    return GetRole(uow=uow)


def get_create_role() -> CreateRole:
    uow = SqlAlchemyUnitOfWork(SessionFactory)
    return CreateRole(uow=uow)
