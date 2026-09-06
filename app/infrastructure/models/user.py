import uuid

from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base
from app.infrastructure.models.mixins import TimestampMixin


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    first_name: Mapped[str] = mapped_column(nullable=False)

    last_name: Mapped[str] = mapped_column(nullable=False)

    email: Mapped[str] = mapped_column(
        nullable=False,
        unique=True,
        index=True,
    )

    password_hash: Mapped[str] = mapped_column(
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        nullable=False,
        default=True,
    )
