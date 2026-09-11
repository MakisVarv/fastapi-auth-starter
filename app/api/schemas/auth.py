from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.api.schemas.user import UserResponse


class RegisterRequest(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: str = Field(min_length=8)


class RegisterResponse(BaseModel):
    id: UUID
    first_name: str
    last_name: str
    email: EmailStr
    is_active: bool


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginResponse(AccessTokenResponse):
    user: UserResponse
