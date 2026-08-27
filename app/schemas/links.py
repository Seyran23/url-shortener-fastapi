from datetime import datetime, timezone
from uuid import UUID

from pydantic import (
    AnyHttpUrl,
    BaseModel,
    ConfigDict,
    Field,
    computed_field,
    field_validator,
)

from app.core.config import settings
from app.core.constants import RESERVED_ALIASES


class LinkCreate(BaseModel):
    original_url: AnyHttpUrl
    custom_alias: str | None = Field(
        default=None, min_length=3, max_length=32, pattern=r"^[a-zA-Z0-9_-]+$"
    )
    max_clicks: int | None = Field(default=None, gt=0)
    expires_at: datetime | None = None

    @field_validator("custom_alias")
    @classmethod
    def validate_alias(cls, v: str | None) -> str | None:
        if v is None:
            return None

        v = v.strip().lower()

        if v in RESERVED_ALIASES:
            raise ValueError(f"'{v}' is reserved and cannot be used as a custom alias")

        return v

    @field_validator("expires_at")
    @classmethod
    def validate_expires_at(cls, v: datetime | None) -> datetime | None:
        return _validate_future_expiry(v)


class LinkResponse(BaseModel):
    id: UUID
    short_code: str

    original_url: str
    expires_at: datetime | None
    max_clicks: int | None
    click_count: int
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @computed_field
    @property
    def short_url(self) -> str:
        return f"{settings.BASE_URL}/{self.short_code}"


class LinkUpdate(BaseModel):
    original_url: AnyHttpUrl | None = None
    max_clicks: int | None = Field(default=None, ge=1)
    expires_at: datetime | None = None
    is_active: bool | None = None

    model_config = ConfigDict(extra="forbid")

    @field_validator("expires_at")
    @classmethod
    def validate_expires_at(cls, v: datetime | None) -> datetime | None:
        return _validate_future_expiry(v)


def _validate_future_expiry(v: datetime | None) -> datetime | None:
    if v is None:
        return v

    aware_v = v if v.tzinfo is not None else v.replace(tzinfo=timezone.utc)

    if aware_v <= datetime.now(timezone.utc):
        raise ValueError("expires_at must be in the future")

    return v
