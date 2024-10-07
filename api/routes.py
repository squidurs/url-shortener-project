from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from models.url_pydantic_models import URLRequest, URLResponse
from service.url_service import *
from datetime import datetime


router = APIRouter()

# Define your API routes here


@router.get("/")
async def read_root():
    return {"message": "Welcome to the URL Shortener API"}

@router.post("/shorten")
async def create_short_url(request: URLRequest):
    try:
        short_url = generate_short_url(request.url, request.custom_url, request.length)
        if request.url:
            response = URLResponse(
                short_url=short_url,
                original_url=request.url,
                timestamp=datetime.now().isoformat()
                )
            return response
        else:
            raise HTTPException(status_code=404, detail="Short URL not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/r/{short_url}")
async def redirect_to_original_url(short_url):
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
    try:
        delete_url(short_url)
        return {"detail": f"{short_url} was deleted."}
    except ValueError:
        raise HTTPException(status_code=404, detail="Short URL not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
        
            
            
            
    

    

