# backend/app/bot/__init__.py

from aiogram import Bot, Dispatcher
from app.config import settings

# Создаём экземпляры бота и диспетчера
bot = Bot(token=settings.BOT_TOKEN)
dp = Dispatcher()

# Экспортием для использования в других модулях
__all__ = ["bot", "dp"]