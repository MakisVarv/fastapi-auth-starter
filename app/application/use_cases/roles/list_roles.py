from collections.abc import Sequence

from app.application.ports.unit_of_work import UnitOfWork
from app.domain.entities.role import Role


class ListRoles:
    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    def execute(self) -> Sequence[Role]:
        with self.uow:
            return self.uow.roles.list_all()
