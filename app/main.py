from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.api import transactions, categories
from app.bot.bot import start_bot
import asyncio
from app.config import settings

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Finance Tracker API")

# main.py — разрешите только ваш домен в продакшене
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.WEBAPP_URL, "https://web.telegram.org"],  # ✅
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(transactions.router)
app.include_router(categories.router)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(start_bot())

@app.get("/")
async def root():
    return {"message": "Finance Tracker API is running"}