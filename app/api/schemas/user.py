from uuid import UUID

from pydantic import BaseModel, EmailStr

from app.api.schemas.common import PaginationParams
from typing import Literal


class UserResponse(BaseModel):
    id: UUID
    first_name: str
    last_name: str
    email: EmailStr
    phone: str | None = None
    is_active: bool


class UserListParams(PaginationParams):
    sort: Literal[
        "id",
        "-id",
        "first_name",
        "-first_name",
        "last_name",
        "-last_name",
        "email",
        "-email",
        "is_active",
        "-is_active",
        "created_at",
        "-created_at",
    ]
