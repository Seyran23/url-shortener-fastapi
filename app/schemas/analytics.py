from datetime import datetime

from pydantic import BaseModel


class AnalyticsSummary(BaseModel):
    total_clicks: int
    unique_visitors: int


class TimeseriesPoint(BaseModel):
    date: datetime
    count: int


class CountryBreakdown(BaseModel):
    country: str | None
    count: int


class DeviceBreakdown(BaseModel):
    device_type: str | None
    count: int


class BrowserBreakdown(BaseModel):
    browser: str | None
    count: int


class ReferrerBreakdown(BaseModel):
    referer: str | None
    count: int
