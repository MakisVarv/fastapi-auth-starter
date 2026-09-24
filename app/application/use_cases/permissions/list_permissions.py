from collections.abc import Sequence

from app.application.ports.unit_of_work import UnitOfWork
from app.domain.entities.permission import Permission


class ListPermissions:
    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    def execute(self) -> Sequence[Permission]:
        with self.uow:
            return self.uow.permissions.list_all()
