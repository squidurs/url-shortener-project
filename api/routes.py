from fastapi import APIRouter, HTTPException, status
from fastapi.responses import RedirectResponse
from models.url_pydantic_models import URLRequest, URLResponse
from pydantic import ValidationError
from service.url_service import *
from datetime import datetime


router = APIRouter()

@router.get("/")
async def read_root():
    """Welcome message for the URL Shortener API.
    """
    return {"message": "Welcome to the URL Shortener API"}

@router.post("/shorten")
async def create_short_url(request: URLRequest):
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
        short_url = generate_short_url(str(request.url), request.custom_url, request.length)
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
    
@router.get("/list_urls")
async def list_url_pairs():
    """Retrieves all stored short-original URL pairs.

    Raises:
        HTTPException: 404 if there are no URLs stored in the database.
        HTTPException: 500 for server errors.

    Returns:
        dict: A dictionary containing all short URLs as keys and their associated original URLs as values.
    """
    try:
        url_list = get_url_list()
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
        
        
            
            
            
    

    

