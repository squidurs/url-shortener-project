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
    
class Token(BaseModel):
    access_token: str
    token_type: str
    
class TokenData(BaseModel):
    username: str = None
    
class UserRequest(BaseModel):
    username: str = Field(default=None, min_length=8, max_length=15, description="Must be between 8 - 15 characters")
    password: str = Field(default=None, min_length=8, max_length=15, description="Must be between 8 - 15 characters")
    
class UserResponse(BaseModel):
    username: str
    url_limit: int
    is_admin: bool
    
class User(BaseModel):
    user_id: str
    hashed_password: str
    url_limit: int = 20
    is_admin: bool = False
    disabled: bool = False
    
    
    
