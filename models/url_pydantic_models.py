from pydantic import BaseModel
from datetime import datetime
from typing import Optional
# Define your models here


class URLRequest(BaseModel):
    url: str
    custom_url: Optional[str] = None
    length: int = 6 #do i need to enforce a minimum? max?


class URLResponse(BaseModel):
    short_url: str
    original_url: str
    timestamp: datetime
