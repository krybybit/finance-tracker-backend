from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Transaction, Category, TransactionType
from app.schemas import TransactionCreate, TransactionResponse
from app.security import validate_telegram_init_data
from typing import List
from datetime import datetime

router = APIRouter(prefix="/api/transactions", tags=["transactions"])

@router.post("/", response_model=TransactionResponse)
def create_transaction(
    transaction: TransactionCreate,
    telegram_init_data: str = Header(...),
    db: Session = Depends(get_db)
):
    if not validate_telegram_init_data(telegram_init_data):
        raise HTTPException(status_code=401, detail="Invalid Telegram data")
    user_id = 1  # В реальном проекте извлекается из initData
    user = db.query(User).filter(User.telegram_id == str(user_id)).first()
    if not user:
        user = User(telegram_id=str(user_id))
        db.add(user)
        db.commit()
        db.refresh(user)
    category = db.query(Category).filter(Category.id == transaction.category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    db_transaction = Transaction(
        amount=transaction.amount,
        type=transaction.type,
        category_id=transaction.category_id,
        user_id=user.id,
        comment=transaction.comment
    )
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction

@router.get("/", response_model=List[TransactionResponse])
def get_transactions(
    telegram_init_data: str = Header(...),
    db: Session = Depends(get_db),
    limit: int = 50,
    offset: int = 0
):
    if not validate_telegram_init_data(telegram_init_data):
        raise HTTPException(status_code=401, detail="Invalid Telegram data")
    user_id = 1
    user = db.query(User).filter(User.telegram_id == str(user_id)).first()
    if not user:
        return []
    transactions = db.query(Transaction).filter(Transaction.user_id == user.id)\
        .order_by(Transaction.created_at.desc()).offset(offset).limit(limit).all()
    return transactions