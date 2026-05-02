from fastapi import APIRouter

from app.api.v1.market import router as market_router

api_router = APIRouter()

api_router.include_router(
    market_router,
    prefix="/market",
    tags=["Market"]
)