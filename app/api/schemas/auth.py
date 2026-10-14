from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

from app.api.schemas.user import UserResponse


class RegisterRequest(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: str | None = None
    password: str = Field(min_length=8)

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_names(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Field cannot be empty.")

        return value

    @field_validator("phone")
    @classmethod
    def normalize_phone(cls, value: str | None) -> str | None:
        if value is None:
            return None

        value = value.strip()
        return value or None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginResponse(AccessTokenResponse):
    user: UserResponse


class ReauthenticateRequest(BaseModel):
    current_password: str = Field(min_length=1)


class ChangePasswordRequest(BaseModel):
    new_password: str = Field(min_length=8)


class ChangeEmailRequest(BaseModel):
    new_email: EmailStr


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8)


class UpdateMeRequest(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None

    @model_validator(mode="after")
    def validate_not_empty(self):
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided.")

        return self

    @field_validator("phone")
    @classmethod
    def normalize_phone(cls, value: str | None) -> str | None:
        if value is None:
            return None

        value = value.strip()
        return value or None

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_names(cls, value: str | None) -> str:
        if value is None:
            raise ValueError("Field cannot be null.")
        if not value.strip():
            raise ValueError("Field cannot be empty.")
        return value.strip()
