from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import Depends, HTTPException, status
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from models.url_pydantic_models import TokenData
from models.pynamodb_model import UserEntry




# Add any utility functions you need here



SECRET_KEY = "010e8a5d8423450fc3f04320b4c605ab"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth_2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def get_user(user_id: str) -> UserEntry:
    """Retrieves user.

    Args:
        user_id (str): The user ID to look up in the database.

    Raises:
        ValueError: If the user does not exist in the database.

    Returns:
        UserEntry: The user object.
    """
    try:
        user = UserEntry.get(user_id)
        return user
    except UserEntry.DoesNotExist:
        raise ValueError("User does not exist.")
    
def authenticate_user(user_id: str, password: str) -> UserEntry:
    """
    Authenticates the user by comparing the provided password with the hashed password.

    Args:
        user_id (str): The user ID to look up in the database.
        password (str): The plaintext password to verify.

    Returns:
        UserEntry: The user object.
    """
    try:
        user = get_user(user_id)
    except ValueError as v:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User not found: {str(v)}")
    if not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect password")
    return user

def create_access_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
        
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth_2_scheme)):
    credential_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials", headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print(f"Decoded JWT payload: {payload}")
        username: str = payload.get("sub")
        if username is None:
            raise credential_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credential_exception
    user = get_user(user_id=token_data.username)
    if not isinstance(user, UserEntry):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return username

async def get_current_active_user(current_user: UserEntry = Depends(get_current_user)):
    if not isinstance(current_user, UserEntry):
        raise HTTPException(status_code=400, detail="Invalid user data")
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    return current_user.user_id