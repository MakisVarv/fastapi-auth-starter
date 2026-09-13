from pydantic import BaseModel, EmailStr, Field

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
