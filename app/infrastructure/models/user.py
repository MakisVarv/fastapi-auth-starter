import uuid

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import BaseModel
from app.infrastructure.models.role import RoleModel


class UserModel(BaseModel):
    __tablename__ = "users"

    first_name: Mapped[str] = mapped_column(nullable=False)

    last_name: Mapped[str] = mapped_column(nullable=False)

    email: Mapped[str] = mapped_column(
        nullable=False,
        unique=True,
        index=True,
    )

    phone: Mapped[str | None] = mapped_column(nullable=True)

    password_hash: Mapped[str] = mapped_column(
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        nullable=False,
        default=True,
    )

    role_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("roles.id", ondelete="RESTRICT"),
        nullable=False,
    )

    role: Mapped["RoleModel"] = relationship(
        "RoleModel",
        back_populates="users",
    )
