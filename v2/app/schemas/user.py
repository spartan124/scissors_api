"""User request/response schemas."""
from pydantic import BaseModel, EmailStr


class UserSignUp(BaseModel):
    full_name: str
    username: str
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    full_name: str
    username: str
    email: EmailStr

    model_config = {"from_attributes": True}


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    username: str
    token_type: str = "bearer"


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
