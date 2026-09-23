from app.application.errors import RoleAlreadyExist
from app.application.ports.unit_of_work import UnitOfWork
from app.domain.entities.role import Role


class CreateRole:
    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    def execute(self, name: str, description: str | None, level: int) -> Role:
        with self.uow:
            existing = self.uow.roles.get_by_name(name=name)
            if existing is not None:
                raise RoleAlreadyExist()
            role = Role(name=name, description=description, level=level)
            self.uow.roles.add(role)
            self.uow.commit()
            return role
