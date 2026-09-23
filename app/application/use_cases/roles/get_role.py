from uuid import UUID

from app.application.errors import RoleNotFoundError
from app.application.ports.unit_of_work import UnitOfWork
from app.domain.entities.role import Role


class GetRole:
    def __init__(
        self,
        uow: UnitOfWork,
    ) -> None:
        self.uow = uow

    def execute(self, role_id: UUID) -> Role:

        with self.uow:
            role = self.uow.roles.get_by_id(role_id)
            if role is None:
                raise RoleNotFoundError()
            return role
