from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import BaseModel
from app.infrastructure.models.role_permission import role_permissions

if TYPE_CHECKING:
    from app.infrastructure.models.role import RoleModel


class PermissionModel(BaseModel):

    __tablename__ = "permissions"

    name: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    roles: Mapped[list["RoleModel"]] = relationship(
        "RoleModel",
        secondary=role_permissions,
        back_populates="permissions",
    )
