from pydantic import BaseModel, HttpUrl, Field
from datetime import datetime
from typing import Optional
# Define your models here


class URLRequest(BaseModel):
    url: HttpUrl
    custom_url: Optional[str] = Field(default=None, min_length=10, max_length=15, description="Length must be between 10 and 15")
    length: int = Field(default=10, ge=10, le=15, description="Length must be between 10 and 15")


class URLResponse(BaseModel):
    short_url: str
    original_url: str
    timestamp: datetime
