from sqlalchemy import func, select

from app.application.common.pagination import Page
from app.application.common.sorting import SortOptions
from app.application.errors import UserNotFoundError
from app.domain.entities.permission import Permission
from app.domain.entities.role import Role
from app.domain.entities.user import User
from app.infrastructure.models import RoleModel
from app.infrastructure.models.user import UserModel
from app.infrastructure.query.sorting import apply_sorting
from app.infrastructure.repositories.base import SqlAlchemyRepository


class SqlAlchemyUserRepository(SqlAlchemyRepository[User, UserModel]):
    model_type = UserModel

    def _to_domain(self, model: UserModel) -> User:
        return User(
            id=model.id,
            first_name=model.first_name,
            last_name=model.last_name,
            email=model.email,
            phone=model.phone,
            password_hash=model.password_hash,
            is_active=model.is_active,
            role=Role(
                id=model.role.id,
                name=model.role.name,
                description=model.role.description,
                level=model.role.level,
                permissions=[
                    Permission(
                        id=permission.id,
                        name=permission.name,
                        description=permission.description,
                    )
                    for permission in model.role.permissions
                ],
            ),
        )

    def list_paginated(
        self,
        *,
        page: int,
        page_size: int,
        sort_options: SortOptions,
    ) -> Page[User]:
        statement = self._base_query()
        count_statement = select(func.count()).select_from(UserModel)
        sort_columns = {
            "id": UserModel.id,
            "first_name": UserModel.first_name,
            "last_name": UserModel.last_name,
            "email": UserModel.email,
            "is_active": UserModel.is_active,
            "created_at": UserModel.created_at,
            "role": RoleModel.name,
        }

        if sort_options.field == "role":
            statement = statement.join(
                RoleModel,
                UserModel.role_id == RoleModel.id,
            )

        statement = apply_sorting(
            statement,
            sort_columns=sort_columns,
            options=sort_options,
            secondary_column=UserModel.id,
        )

        return self._paginate(
            statement=statement,
            count_statement=count_statement,
            page=page,
            page_size=page_size,
        )

    def get_by_email(self, email: str) -> User | None:
        model = self.session.scalar(select(UserModel).where(UserModel.email == email))
        if model is None:
            return None

        return self._to_domain(model)

    def add(self, user: User) -> None:

        model = UserModel(
            id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            role_id=user.role.id,
            phone=user.phone,
            password_hash=user.password_hash,
            is_active=user.is_active,
        )

        self.session.add(model)

    def update(self, user: User) -> None:
        model = self.session.scalar(select(UserModel).where(UserModel.id == user.id))
        if model is None:
            raise UserNotFoundError()
        model.first_name = user.first_name
        model.last_name = user.last_name
        model.email = user.email
        model.role_id = user.role.id
        model.phone = user.phone
        model.password_hash = user.password_hash
        model.is_active = user.is_active
