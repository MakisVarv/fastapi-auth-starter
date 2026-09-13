from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

from app.api.schemas.user import UserResponse


class RegisterRequest(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: str | None = None
    password: str = Field(min_length=8)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginResponse(AccessTokenResponse):
    user: UserResponse


class UpdateMeRequest(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None

    @model_validator(mode="after")
    def validate_not_empty(self):
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided.")

        return self

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_names(cls, value: str | None) -> str:
        if value is None:
            raise ValueError("Field cannot be null.")
        if not value.strip():
            raise ValueError("Field cannot be empty.")
        return value.strip()
