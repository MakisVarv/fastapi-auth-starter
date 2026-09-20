from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.api.schemas.common import PaginationParams
from app.api.schemas.role import RoleResponse


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    first_name: str
    last_name: str
    email: EmailStr
    phone: str | None = None
    is_active: bool
    role: RoleResponse


class CreateUserRequest(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: str | None = None
    password: str = Field(min_length=8)
    role_id: UUID


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
        "role",
        "-role",
        "created_at",
        "-created_at",
    ] = "-created_at"
    search: str | None = None
    role: str | None = None
    is_active: bool | None = None
