from pydantic import BaseModel


class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterResponse(BaseModel):
    message: str
    assigned_plan: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str


class UpgradeResponse(BaseModel):
    message: str
    note: str | None = None


class CurrentUserResponse(BaseModel):
    id: int
    name: str
    email: str
