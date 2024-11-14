from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from models.url_pydantic_models import *
from pydantic import ValidationError
from service.exceptions import *
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
async def create_short_url(request: URLRequest, user: UserEntry = Depends(get_current_user)):
    """Creates a short URL for a given original URL.

    Args:
        request (URLRequest): The request body containing the original URL, optional custom URL, and optional short URL length.
        token (str): Bearer token for authentication.
    
    Raises:
        HTTPException: 422 if the provided URL format is invalid.
        HTTPException: 403 if the URL limit is reached
        HTTPException: 409 if the custom URL is already in use.
        HTTPException: 400 if no URL is provided in the request.
        HTTPException: 500 for general server errors.

    Returns:
        URLResponse: An object containing the generated short URL, the original URL, and a timestamp.
    """
    try:
        short_url = generate_short_url(str(request.url), user.user_id, request.custom_url, request.length)
        if request.url:
            response = URLResponse(
                short_url=short_url,
                original_url=str(request.url),
                timestamp=datetime.now().isoformat()
                )
            return response
        else:
            raise HTTPException(status_code=400, detail="Please provide a URL")
    except ValidationError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail = "The provided URL is invalid. Please provide a valid URL.")
    except UrlLimitReachedError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except CustomUrlExistsError as e:
        raise HTTPException(status_code=409, detail=str(e))
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
async def list_url_pairs(user: UserEntry = Depends(get_current_user)):
    """Retrieves all stored short-original URL pairs.

    Args:
        token (str): Bearer token for authentication.
    
    Raises:
        HTTPException: 403 for non-admin users
        HTTPException: 404 if there are no URLs stored in the database.
        HTTPException: 500 for server errors.

    Returns:
        dict: All short URLs as keys and their associated original URLs as values.
    """
    
    try:
        validate_admin_user(user)
        url_list = get_url_list()
        if url_list:
            return {"url_pairs": url_list}
        else:
            raise HTTPException(status_code=404, detail="No URLs found")
    except ValueError as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}") 
    except AdminPrivilegesRequiredError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@router.get("/list-my-urls")
async def list_my_urls(user: UserEntry = Depends(get_current_user)):
    """Lists URLs specific to the authenticated user.

    Args:
        token (str): Bearer token for authentication.

    Raises:
        HTTPException: 404 if no URLs are found for the user.
        HTTPException: 500 for server errors.

    Returns:
        dict: URLs associated with the authenticated user.
    """    
    try:
        url_list = get_user_url_list(user.user_id)
        if url_list:
            return {"url_pairs": url_list}
        else:
            raise HTTPException(status_code=404, detail="No URLs found")
    except JWTError:
        raise HTTPException(HTTPExceptionstatus_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials", headers={"WWW-Authenticate": "Bearer"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    
@router.delete("/delete-url/{short_url}")
async def delete_url(short_url, user: UserEntry = Depends(get_current_user)):
    """Deletes a given short URL from the database.

    Args:
        short_url (str): The short URL to be deleted.
        token (str): Bearer token for authentication.

    Raises:
        HTTPException: 403 if user is not admin.
        HTTPException: 404 if the short URL is not found in the database.
        HTTPException: 500 for server errors.

    Returns:
        dict: A message confirming that the specified short URL was deleted.
    """
    
    try:
        #AUTHENTICATE ADMIN
        validate_admin_user(user)
        delete_url(user, short_url)
        return {"detail": f"{short_url} was deleted."}
    except AdminPrivilegesRequiredError:
        raise HTTPException(status_code=403, detail="Admin privileges required.")
    except ValueError:
        raise HTTPException(status_code=404, detail="Short URL not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
       
@router.post("/create-user")
async def create_user(user_request: UserRequest):
    """Creates a new user account.

    Args:
        user_request (UserRequest): The request body containing user credentials.

    Returns:
        dict: Confirmation message that the user was created successfully.
    """
    new_user = create_new_user(user_request.username, user_request.password)
    return {"message": f"User {new_user.user_id} created successfully."}
    

@router.post("/login", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm=Depends()):
    """Authenticates a user and generates an access token.

    Args:
        form_data (OAuth2PasswordRequestForm): Form containing username and password.

    Raises:
        HTTPException: 401 if credentials are incorrect.

    Returns:
        dict: Access token and token type.
    """
    user = authenticate_user(form_data.username, form_data.password) 
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password", headers={"WWW-Authenticate": "Bearer"})
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub":user.user_id}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}
    


@router.post("/change-password")
async def change_password(user_request: UserRequest, user: UserEntry = Depends(get_current_user)):
    """Changes the password for the authenticated user.

    Args:
        user_request (UserRequest): The request body containing the new password.
        token (str): Bearer token for authentication.

    Returns:
        dict: Confirmation message that the password was updated.
    """
    try:
        update_password(user.user_id, user_request.password)
        return {"message": "Password has been updated."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@router.post("/update-url-limit")
async def update_url_limit(request: UpdateUrlLimitRequest, user: UserEntry = Depends(get_current_user)):
    """Updates the URL limit for a specific user.

    Args:
        user_id (str): The username of the user whose limit is being updated.
        new_limit (int): The new URL limit to be set for the user.
        token (str): Bearer token for authentication.

    Raises:
        HTTPException: 403 if the user (token bearer) is not admin.
        HTTPException: 404 if the user (to be updated) is not found.
        HTTPException: 500 for server errors.

    Returns:
        dict: Confirmation message with updated URL limit for the specified user.
    """
    user_to_update = request.user_to_update
    new_limit = request.new_limit
    try:
        validate_admin_user(user)
        user_to_update = UserEntry.get(user_to_update)
        user_to_update.update(actions=[UserEntry.url_limit.set(new_limit)])
        return {"message": f"User {user_to_update.user_id} limit updated to {new_limit}."}
    except UserEntry.DoesNotExist:
        raise HTTPException(status_code=404, detail="User not found.")          
    except AdminPrivilegesRequiredError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except HTTPException as e:
        raise e 
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
            
            
            
    

        
        
            
            
            
    

    

