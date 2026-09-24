from collections.abc import Sequence
from typing import Tuple

from sqlalchemy import Select, select
from sqlalchemy.orm import selectinload

from app.application.errors import PermissionNotFoundError, RoleNotFoundError
from app.domain.entities.permission import Permission
from app.domain.entities.role import Role
from app.infrastructure.models import PermissionModel, RoleModel
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

    def list_all(self) -> Sequence[Role]:
        statement = self._base_query()
        roles = self.session.scalars(statement).all()

        return [self._to_domain(role) for role in roles]

    def get_by_name(self, name: str) -> Role | None:

        stmt = self._base_query().where(RoleModel.name == name)

        model = self.session.execute(stmt).scalar_one_or_none()
        if model is None:
            return None

        return self._to_domain(model=model)

    def add(self, role: Role) -> None:

        model = RoleModel(
            id=role.id, name=role.name, description=role.description, level=role.level
        )

        self.session.add(model)

    def update(self, role: Role) -> None:
        model = self.session.scalar(select(RoleModel).where(RoleModel.id == role.id))
        if model is None:
            raise RoleNotFoundError()
        model.name = role.name
        model.description = role.description
        model.level = role.level

    def assign_permission(self, role: Role, permission: Permission) -> None:
        role_model = self.session.get(RoleModel, role.id)
        permission_model = self.session.get(PermissionModel, permission.id)

        if role_model is None:
            raise RoleNotFoundError()

        if permission_model is None:
            raise PermissionNotFoundError()

        role_model.permissions.append(permission_model)

    def remove_permission(self, role: Role, permission: Permission) -> None:
        role_model = self.session.get(RoleModel, role.id)
        permission_model = self.session.get(PermissionModel, permission.id)

        if role_model is None:
            raise RoleNotFoundError()

        if permission_model is None:
            raise PermissionNotFoundError()

        role_model.permissions.remove(permission_model)
