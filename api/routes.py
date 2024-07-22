from fastapi import APIRouter

router = APIRouter()

# Define your API routes here


@router.get("/")
async def read_root():
    return {"message": "Welcome to the URL Shortener API"}
