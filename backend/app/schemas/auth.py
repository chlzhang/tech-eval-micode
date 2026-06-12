"""
认证相关 Schema
"""

from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserInfo(BaseModel):
    id: int
    username: str
    display_name: str | None = None
    department: str | None = None
    role: str
    is_active: bool
    
    class Config:
        from_attributes = True
