from app.application.use_cases.roles.list_roles import ListRoles
from app.infrastructure.database.session import SessionFactory
from app.infrastructure.uow.sqlalchemy import SqlAlchemyUnitOfWork


def get_list_roles() -> ListRoles:
    uow = SqlAlchemyUnitOfWork(SessionFactory)
    return ListRoles(uow=uow)
