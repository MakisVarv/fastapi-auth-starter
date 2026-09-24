from collections.abc import Sequence

from app.domain.entities.permission import Permission
from app.infrastructure.models import PermissionModel
from app.infrastructure.repositories.base import SqlAlchemyRepository


class SqlAlchemyPermissionRepository(SqlAlchemyRepository[Permission, PermissionModel]):

    def _to_domain(self, model: PermissionModel) -> Permission:
        return Permission(id=model.id, name=model.name, description=model.description)

    def list_all(self) -> Sequence[Permission]:
        statement = self._base_query()
        permissions = self.session.scalars(statement).all()

        return [self._to_domain(permission) for permission in permissions]
