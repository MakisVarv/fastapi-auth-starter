from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.api.schemas.permission import PermissionResponse
from app.domain.authorization import MAX_ROLE_LEVEL


class RoleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    description: str | None = None
    level: int
    permissions: list[PermissionResponse]


class CreateRoleRequest(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    description: str | None = Field(default=None, max_length=255)
    level: int = Field(ge=1, le=MAX_ROLE_LEVEL)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Field cannot be empty.")

        return value


class AddPermissionRequest(BaseModel):

    permission_id: UUID


class UpdateRoleRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=50)
    description: str | None = Field(default=None, max_length=255)
    level: int | None = Field(default=None, ge=1, le=MAX_ROLE_LEVEL)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str | None) -> str:
        if value is None:
            raise ValueError("Field cannot be null.")

        value = value.strip()

        if not value:
            raise ValueError("Field cannot be empty.")

        return value

    @field_validator("level")
    @classmethod
    def validate_level(cls, value: int | None) -> int:
        if value is None:
            raise ValueError("Field cannot be null.")

        return value

    @model_validator(mode="after")
    def validate_not_empty(self):
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided.")

        return self
