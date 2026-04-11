from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Category, User
from app.schemas import CategoryCreate, CategoryResponse
from app.security import validate_telegram_init_data, get_user_from_init_data

from typing import List

router = APIRouter(prefix="/categories", tags=["categories"])

@router.post("/", response_model=CategoryResponse)
def create_category(
    category: CategoryCreate,
    telegram_init_data: str = Header(...),
    db: Session = Depends(get_db)
):
    if not validate_telegram_init_data(telegram_init_data):
        raise HTTPException(status_code=401, detail="Invalid Telegram data")
    
    user_info = get_user_from_init_data(telegram_init_data)
    telegram_id = str(user_info['id'])
    
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db_category = Category(
        name=category.name,
        icon=category.icon,
        user_id=user.id
    )
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

@router.get("/", response_model=List[CategoryResponse])
def get_categories(
    telegram_init_data: str = Header(...),
    db: Session = Depends(get_db)
):
    if not validate_telegram_init_data(telegram_init_data):
        raise HTTPException(status_code=401, detail="Invalid Telegram data")
    
    user_info = get_user_from_init_data(telegram_init_data)
    telegram_id = str(user_info['id'])
    
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        return []
    
    categories = db.query(Category).filter(
        (Category.user_id == user.id) | (Category.user_id == None)
    ).all()
    return categories