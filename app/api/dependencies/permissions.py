from app.application.use_cases.permissions.get_permission import GetPermission
from app.application.use_cases.permissions.list_permissions import ListPermissions
from app.infrastructure.database.session import SessionFactory
from app.infrastructure.uow.sqlalchemy import SqlAlchemyUnitOfWork


def get_list_permissions() -> ListPermissions:
    uow = SqlAlchemyUnitOfWork(SessionFactory)
    return ListPermissions(uow=uow)


def get_permission_use_case() -> GetPermission:
    uow = SqlAlchemyUnitOfWork(SessionFactory)
    return GetPermission(uow=uow)
