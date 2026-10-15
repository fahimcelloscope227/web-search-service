from fastapi import APIRouter

from app.api.v1.routes import search

api_router = APIRouter()
api_router.include_router(search.router)
