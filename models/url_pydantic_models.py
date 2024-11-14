from pydantic import BaseModel, HttpUrl, Field, ValidationError, validator
from datetime import datetime
from typing import Optional

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
    username: str = Field(default=None, min_length=8, max_length=15,
        description="Username must be between 8 - 15 characters and contain only letters and numbers")
    password: str = Field(default=None, min_length=8, max_length=15,
        description="Password must be between 8 - 15 characters, include at least one uppercase letter, one lowercase letter, one number, and one special character")
    
    @validator('username')
    def validate_username(cls, username):
        if not username.isalnum() or not (8 <= len(username) <= 15):
            raise ValueError("Username must be between 8 - 15 characters and contain only letters and numbers")
        return username

    @validator('password')
    def validate_password(cls, password):
        if (not any(c.isdigit() for c in password) or
                not any(c.islower() for c in password) or
                not any(c.isupper() for c in password) or
                not any(c in '@$!%*?&' for c in password)):
            raise ValueError("Password must be between 8 - 15 characters, include at least one uppercase letter, one lowercase letter, one number, and one special character")
        return password
    
class UpdateUrlLimitRequest(BaseModel):
    user_to_update: str
    new_limit: int
    
    
