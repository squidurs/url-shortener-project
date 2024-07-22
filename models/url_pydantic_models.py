from pydantic import BaseModel
# Define your models here


class URLRequest(BaseModel):
    url: str


class URLResponse(BaseModel):
    short_url: str
    original_url: str
    timestamp: str
