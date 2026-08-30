import uuid
from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    computed_field,
    field_validator,
)

from app.schemas.token import Token


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(not c.isalnum() for c in v):
            raise ValueError("Password must contain at least one symbol")
        return v

    
class UserResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    created_at: datetime
    telegram_chat_id: int | None = Field(default=None, exclude=True)

    model_config = ConfigDict(from_attributes=True)

    @computed_field
    @property
    def telegram_linked(self) -> bool:
        return self.telegram_chat_id is not None
    

class RegisterResponse(BaseModel):
    user: UserResponse
    token: Token


class TelegramLinkCodeResponse(BaseModel):
    code: str
    expires_in_seconds: int
