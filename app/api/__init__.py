# backend/app/api/__init__.py

from fastapi import APIRouter
from app.api.transactions import router as transactions_router
from app.api.categories import router as categories_router

# Создаём главный API роутер
api_router = APIRouter(prefix="/api")

# Включаем все маршруты
api_router.include_router(transactions_router)
api_router.include_router(categories_router)

# Экспортием для использования в main.py
__all__ = ["api_router"]