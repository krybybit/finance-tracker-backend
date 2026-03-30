from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Transaction, Category, TransactionType
from app.schemas import TransactionCreate, TransactionResponse
from app.security import validate_telegram_init_data, get_user_from_init_data
from typing import List
from datetime import datetime
from sqlalchemy import func, extract
from sqlalchemy.sql import label


# ✅ УБРАЛИ /api из префикса (главный роутер уже добавит /api)
router = APIRouter(prefix="/transactions", tags=["transactions"])

@router.post("/", response_model=TransactionResponse)
def create_transaction(
    transaction: TransactionCreate,
    telegram_init_data: str = Header(...),
    db: Session = Depends(get_db)
):
    if not validate_telegram_init_data(telegram_init_data):
        raise HTTPException(status_code=401, detail="Invalid Telegram data")
    
    # ✅ ИЗВЛЕКАЕМ РЕАЛЬНОГО ПОЛЬЗОВАТЕЛЯ
    user_info = get_user_from_init_data(telegram_init_data)
    telegram_id = str(user_info['id'])
    
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        user = User(telegram_id=telegram_id, username=user_info.get('username'))
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
    
    # ✅ ИЗВЛЕКАЕМ РЕАЛЬНОГО ПОЛЬЗОВАТЕЛЯ
    user_info = get_user_from_init_data(telegram_init_data)
    telegram_id = str(user_info['id'])
    
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        return []
    
    transactions = db.query(Transaction).filter(Transaction.user_id == user.id)\
        .order_by(Transaction.created_at.desc()).offset(offset).limit(limit).all()
    return transactions

@router.get("/statistics", response_model=dict)
def get_statistics(
    telegram_init_data: str = Header(...),
    db: Session = Depends(get_db)
):
    if not validate_telegram_init_data(telegram_init_data):
        raise HTTPException(status_code=401, detail="Invalid Telegram data")
    
    user_info = get_user_from_init_data(telegram_init_data)
    telegram_id = str(user_info['id'])
    
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        return {"total_income": 0, "total_expense": 0, "balance": 0, "by_category": []}
    
    # Общая статистика
    total_income = db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == user.id,
        Transaction.type == TransactionType.INCOME
    ).scalar() or 0
    
    total_expense = db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == user.id,
        Transaction.type == TransactionType.EXPENSE
    ).scalar() or 0
    
    # По категориям
    category_stats = db.query(
        Category.name,
        Category.icon,
        func.sum(Transaction.amount).label('total'),
        func.count(Transaction.id).label('count')
    ).join(
        Transaction, Category.id == Transaction.category_id
    ).filter(
        Transaction.user_id == user.id,
        Transaction.type == TransactionType.EXPENSE
    ).group_by(Category.id, Category.name, Category.icon).all()
    
    by_category = [
        {
            "category": cat.name,
            "icon": cat.icon,
            "total": float(cat.total),
            "count": cat.count
        }
        for cat in category_stats
    ]
    
    return {
        "total_income": float(total_income),
        "total_expense": float(total_expense),
        "balance": float(total_income - total_expense),
        "by_category": by_category
    }

@router.delete("/{transaction_id}")
def delete_transaction(
    transaction_id: int,
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
    
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == user.id
    ).first()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    db.delete(transaction)
    db.commit()
    
    return {"message": "Transaction deleted successfully"}