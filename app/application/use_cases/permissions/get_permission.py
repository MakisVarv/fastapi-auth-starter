from uuid import UUID

from app.application.errors import PermissionNotFoundError
from app.application.ports.unit_of_work import UnitOfWork
from app.domain.entities.permission import Permission


class GetPermission:
    def __init__(
        self,
        uow: UnitOfWork,
    ) -> None:
        self.uow = uow

    def execute(self, permission_id: UUID) -> Permission:

        with self.uow:
            permission = self.uow.permissions.get_by_id(permission_id)
            if permission is None:
                raise PermissionNotFoundError()
            return permission
