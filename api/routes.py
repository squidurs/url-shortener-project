from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from models.url_pydantic_models import *
from pydantic import ValidationError
from service.url_service import *
from service.utils import *
from datetime import datetime, timedelta


router = APIRouter()

@router.get("/")
async def read_root():
    """Welcome message for the URL Shortener API.
    """
    return {"message": "Welcome to the URL Shortener API"}

@router.post("/shorten")
async def create_short_url(request: URLRequest, token: str=Depends(oauth_2_scheme)):
    """Creates a short URL for a given original URL.

    Args:
        request (URLRequest): The request body containing the original URL, optional custom URL, and optional short URL length.

    Raises:
        HTTPException: 422 if the provided URL format is invalid.
        HTTPException: 409 if the custom URL is already in use.
        HTTPException: 404 if no URL is provided in the request.
        HTTPException: 500 for general server errors.

    Returns:
        URLResponse: An object containing the generated short URL, the original URL, and a timestamp.
    """
    try:
        user = await get_current_user(token)
        short_url = generate_short_url(str(request.url), user, request.custom_url, request.length)
        if request.url:
            response = URLResponse(
                short_url=short_url,
                original_url=str(request.url),
                timestamp=datetime.now().isoformat()
                )
            return response
        else:
            raise HTTPException(status_code=404, detail="Short URL not found.")
    except ValidationError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail = "The provided URL is invalid. Please provide a valid URL.")
    except ValueError as ve:
        raise HTTPException(status_code=409, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/r/{short_url}")
async def redirect_to_original_url(short_url):
    """Redirects to the original URL corresponding to a given short URL.

    Args:
        short_url (str): The short URL that maps to the original URL.

    Raises:
        HTTPException: 404 if the short URL is not found in the database.
        HTTPException: 500 for server errors.

    Returns:
        RedirectResponse: A redirection to the original URL.
    """
    try:
        #call service func to get og url
        original_url = get_original_url(short_url)
        #redirect to og url
        return RedirectResponse(url=original_url)
    except ValueError:
        #short url not in db
        raise HTTPException(status_code=404, detail="Short URL not found")
    except Exception as e:
        #server error
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/list-urls")
async def list_url_pairs(token: str = Depends(oauth_2_scheme)):
    """Retrieves all stored short-original URL pairs.

    Raises:
        HTTPException: 404 if there are no URLs stored in the database.
        HTTPException: 500 for server errors.

    Returns:
        dict: A dictionary containing all short URLs as keys and their associated original URLs as values.
    """
    username = await get_current_user(token)
    user = get_user(username)
    try:
        #AUTHENTICATE ADMIN
        if user.is_admin:
            url_list = get_url_list()
            if url_list:
                return {"url_pairs": url_list}
            else:
                raise HTTPException(status_code=404, detail="No URLs found")
        else:
            raise HTTPException(status_code=403, detail="Admin privileges required.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@router.get("/list-my-urls")
async def list_my_urls(token: str = Depends(oauth_2_scheme)):    
    username = await get_current_user(token)
    try:
        url_list = get_user_url_list(username)
        if url_list:
            return {"url_pairs": url_list}
        else:
            raise HTTPException(status_code=404, detail="No URLs found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    
@router.delete("/delete-url/{short_url}")
async def delete_url(short_url):
    """Deletes a given short URL from the database.

    Args:
        short_url (str): The short URL to be deleted.

    Raises:
        HTTPException: 404 if the short URL is not found in the database.
        HTTPException: 500 for server errors.

    Returns:
        dict: A message confirming that the specified short URL was deleted.
    """
    try:
        delete_url(short_url)
        return {"detail": f"{short_url} was deleted."}
    except ValueError:
        raise HTTPException(status_code=404, detail="Short URL not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
       
@router.post("/create-user", response_model=UserResponse)
async def create_user(user_request: UserRequest):
    #call create new user func from url service..
    new_user = create_new_user(user_request.username, user_request.password)
    return UserResponse(
        username=new_user.user_id,
        url_limit=new_user.url_limit,
        is_admin=new_user.is_admin
    )
    

@router.post("/login", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm=Depends()):
    user = authenticate_user(form_data.username, form_data.password) 
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password", headers={"WWW-Authenticate": "Bearer"})
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub":user.user_id}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}
    


@router.post("/change-password")
async def change_password(user_request: UserRequest, token: str = Depends(oauth_2_scheme)):
    
    user = await get_current_user(token)
    try:
        update_password(user, user_request.password)
        return {"message": "Password has been updated."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@router.post("/update-url-limit")
async def update_url_limit(user_id: str, new_limit: int, token: str=Depends(oauth_2_scheme)):
    username = await get_current_user(token)
    user = get_user(username)
    try:
        #AUTHENTICATE ADMIN
        if not user.is_admin:
            raise HTTPException(status_code=403, detail="Admin privileges required.")
        try:
            user_to_update = UrlEntry.get(user_id)
            user_to_update.update(actions=[
            UserEntry.url_limit.set(new_limit)])
            return {"message": f"User {user_id} limit updated to {new_limit}."}
        except UserEntry.DoesNotExist:
            raise HTTPException(status_code=404, detail="User not found.")          
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
            
            
            
    

        
        
            
            
            
    

    

