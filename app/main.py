from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.api import api_router  
from app.bot.bot import start_bot
import asyncio
from app.config import settings
from app.models import Category

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Finance Tracker API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

@app.on_event("startup")
async def startup_event():
    # Создаём категории при старте
    from sqlalchemy.orm import Session
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        default_categories = [
            {"name": "🍔 Продукты", "icon": "🍔"},
            {"name": "🚗 Транспорт", "icon": "🚗"},
            {"name": "💼 Зарплата", "icon": "💼"},
            {"id": 4, "name": "Прочее", "icon": "🔹"},
        ]
        for cat in default_categories:
            if not db.query(Category).filter(Category.name == cat["name"]).first():
                db.add(Category(**cat))
        db.commit()
    finally:
        db.close()
    
    asyncio.create_task(start_bot())

@app.get("/")
async def root():
    return {"message": "Finance Tracker API is running"}