from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict, model_validator


class UserBase(BaseModel):
    first_name: str = Field(min_length=1, max_length=50, description="User's first name")
    last_name: str = Field(min_length=1, max_length=50, description="User's last name")
    email: EmailStr = Field(description="User's email address")
    username: str = Field(min_length=3, max_length=50, description="User's unique username")

    model_config = ConfigDict(from_attributes=True)


class UserCreate(UserBase):
    """Schema for registration. Requires password + confirm_password to match."""

    password: str = Field(min_length=8, max_length=128, description="Password (8-128 chars)")
    confirm_password: str = Field(min_length=8, max_length=128, description="Repeat password")

    @model_validator(mode="after")
    def passwords_match(self) -> "UserCreate":
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self

    @model_validator(mode="after")
    def password_strength(self) -> "UserCreate":
        password = self.password
        if not any(c.isupper() for c in password):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in password):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in password):
            raise ValueError("Password must contain at least one digit")
        return self

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "first_name": "John",
                "last_name": "Doe",
                "email": "john.doe@example.com",
                "username": "johndoe",
                "password": "SecurePass123",
                "confirm_password": "SecurePass123",
            }
        }
    )


class UserLogin(BaseModel):
    """Schema for login. Accepts either username or email in `username`."""

    username: str = Field(min_length=3, max_length=50, description="Username or email")
    password: str = Field(min_length=8, max_length=128)

    model_config = ConfigDict(
        json_schema_extra={"example": {"username": "johndoe", "password": "SecurePass123"}}
    )


class UserResponse(BaseModel):
    """Schema returned to clients. Never includes the password."""

    id: UUID
    username: str
    email: EmailStr
    first_name: str
    last_name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
    