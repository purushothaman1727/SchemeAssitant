from fastapi import APIRouter

from app.api import admin, chat, health, profile, schemes

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(profile.router, tags=["profile"])
api_router.include_router(schemes.router, tags=["schemes"])
api_router.include_router(chat.router, tags=["chat"])
api_router.include_router(admin.router)
