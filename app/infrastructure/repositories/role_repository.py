from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.domain.entities.permission import Permission
from app.domain.entities.role import Role
from app.infrastructure.models import RoleModel


class SqlAlchemyRoleRepository:

    def __init__(self, session: Session):
        self.session = session

    def get_by_name(self, name: str) -> Role | None:

        stmt = (
            select(RoleModel)
            .options(selectinload(RoleModel.permissions))
            .where(RoleModel.name == name)
        )

        model = self.session.execute(stmt).scalar_one_or_none()
        if model is None:
            return None

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
