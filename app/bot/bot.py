from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import WebAppInfo
from app.config import settings

bot = Bot(token=settings.BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text="💰 Открыть финансы", web_app=WebAppInfo(url=settings.WEBAPP_URL))]],
        resize_keyboard=True
    )
    await message.answer(
        "Добро пожаловать в Финансовый Трекер!\nНажмите кнопку ниже, чтобы начать.",
        reply_markup=keyboard
    )

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(
        "📊 Доступные команды:\n"
        "/start - Запустить бота\n"
        "/help - Показать справку\n"
        "Используйте кнопку меню для открытия приложения."
    )

async def start_bot():
    await dp.start_polling(bot)