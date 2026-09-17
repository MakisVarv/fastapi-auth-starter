from typing import Tuple

from sqlalchemy import Select
from sqlalchemy.orm import Session, selectinload

from app.domain.entities.permission import Permission
from app.domain.entities.role import Role
from app.infrastructure.models import RoleModel
from app.infrastructure.repositories.base import SqlAlchemyRepository


class SqlAlchemyRoleRepository(SqlAlchemyRepository[Role, RoleModel]):
    model_type = RoleModel

    def _base_query(self) -> Select[Tuple[RoleModel]]:
        return super()._base_query().options(selectinload(RoleModel.permissions))

    def _to_domain(self, model: RoleModel) -> Role:
        return Role(
            id=model.id,
            name=model.name,
            description=model.description,
            level=model.level,
            permissions=[
                Permission(
                    id=permission_model.id,
                    name=permission_model.name,
                    description=permission_model.description,
                )
                for permission_model in model.permissions
            ],
        )

    def get_by_name(self, name: str) -> Role | None:

        stmt = self._base_query().where(RoleModel.name == name)

        model = self.session.execute(stmt).scalar_one_or_none()
        if model is None:
            return None

        return self._to_domain(model=model)
