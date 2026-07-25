from pydantic import BaseModel, Field, ConfigDict


class TokenResponse(BaseModel):
    """Schema returned on successful login."""

    access_token: str = Field(description="JWT access token")
    token_type: str = Field(default="bearer")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                "token_type": "bearer",
            }
        }
    )
    