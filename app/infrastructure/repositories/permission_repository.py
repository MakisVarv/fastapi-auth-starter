from collections.abc import Sequence

from app.domain.entities.permission import Permission
from app.infrastructure.models import PermissionModel
from app.infrastructure.repositories.base import SqlAlchemyRepository


class SqlAlchemyPermissionRepository(SqlAlchemyRepository[Permission, PermissionModel]):
    model_type = PermissionModel

    def _to_domain(self, model: PermissionModel) -> Permission:
        return Permission(id=model.id, name=model.name, description=model.description)

    def get_by_name(self, name: str) -> Permission | None:
        model = self.session.scalar(
            self._base_query().where(PermissionModel.name == name)
        )
        if model is None:
            return None
        return self._to_domain(model)

    def list_all(self) -> Sequence[Permission]:
        statement = self._base_query()
        permissions = self.session.scalars(statement).all()

        return [self._to_domain(permission) for permission in permissions]

    def add(self, permission: Permission) -> None:
        model = PermissionModel(
            id=permission.id,
            name=permission.name,
            description=permission.description,
        )
        self.session.add(model)

    def update(self, permission: Permission) -> None:
        model = self.session.get(PermissionModel, permission.id)

        if model is None:
            return

        model.name = permission.name
        model.description = permission.description
