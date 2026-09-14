from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import BaseModel
from app.infrastructure.models.user import UserModel


class RoleModel(BaseModel):

    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    level: Mapped[int] = mapped_column(Integer, nullable=False)

    users: Mapped[list["UserModel"]] = relationship(
        "User",
        back_populates="role",
    )
