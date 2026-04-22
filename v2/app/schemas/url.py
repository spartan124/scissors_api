"""URL request/response schemas."""
from datetime import datetime

from pydantic import BaseModel


class ShortenRequest(BaseModel):
    original_url: str
    short_code: str | None = None


class ShortenResponse(BaseModel):
    shortened_url: str
    short_code: str


class UrlOut(BaseModel):
    id: int
    original_url: str
    short_code: str
    created_at: datetime
    click_count: int

    model_config = {"from_attributes": True}


class UrlHistoryItem(BaseModel):
    short_code: str
    shortened_url: str


class AnalyticsData(BaseModel):
    short_code: str
    original_url: str
    total_clicks: int
    clicks_by_source: dict[str, int]
