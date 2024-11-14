from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status
from datetime import datetime, timedelta
from jose import ExpiredSignatureError, JWTError, jwt
from passlib.context import CryptContext
from models.url_pydantic_models import TokenData
from models.pynamodb_model import UserEntry
import boto3
import json
from botocore.exceptions import ClientError


def get_secret():

    secret_name = "url-shortener/jwt_secret"
    region_name = "us-east-2"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        print(f"Error retrieving secret: {e}") 
        raise e

    secret = get_secret_value_response['SecretString']
    secret_dict = json.loads(secret)
    
    jwt_key =secret_dict['JWT_SECRET_KEY']
    
    return jwt_key

SECRET_KEY = get_secret()
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


async def get_current_user(token: str = Depends(oauth_2_scheme)) -> UserEntry:
    credential_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials", headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credential_exception
        token_data = TokenData(username=username)
    except ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired", headers={"WWW-Authenticate": "Bearer"})
    except JWTError:
        raise credential_exception
    user = get_user(user_id=token_data.username)
    if not isinstance(user, UserEntry):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user
