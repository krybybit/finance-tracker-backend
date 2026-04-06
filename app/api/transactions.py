from fastapi import APIRouter, Depends, HTTPException, Header, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Transaction, Category, TransactionType
from app.schemas import TransactionCreate, TransactionResponse, TransactionUpdate
from app.security import validate_telegram_init_data, get_user_from_init_data
from typing import List, Optional
from datetime import datetime
from sqlalchemy import func, extract
from sqlalchemy.sql import label

router = APIRouter(prefix="/transactions", tags=["transactions"])

@router.post("/", response_model=TransactionResponse)
def create_transaction(
    transaction: TransactionCreate,
    telegram_init_data: str = Header(...),
    db: Session = Depends(get_db)
):
    if not validate_telegram_init_data(telegram_init_data):
        raise HTTPException(status_code=401, detail="Invalid Telegram data")
    
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
    
    user_info = get_user_from_init_data(telegram_init_data)
    telegram_id = str(user_info['id'])
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    
    if not user:
        return []
    
    transactions = db.query(Transaction).filter(Transaction.user_id == user.id)\
        .order_by(Transaction.created_at.desc()).offset(offset).limit(limit).all()
    return transactions

@router.get("/filter", response_model=List[TransactionResponse])
def filter_transactions(
    telegram_init_data: str = Header(...),
    db: Session = Depends(get_db),
    type: Optional[str] = Query(None),
    category_id: Optional[int] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(50),
    offset: int = Query(0)
):
    if not validate_telegram_init_data(telegram_init_data):
        raise HTTPException(status_code=401, detail="Invalid Telegram data")
    
    user_info = get_user_from_init_data(telegram_init_data)
    telegram_id = str(user_info['id'])
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    
    if not user:
        return []
    
    query = db.query(Transaction).filter(Transaction.user_id == user.id)
    
    if type:
        query = query.filter(Transaction.type == type)
    
    if category_id:
        query = query.filter(Transaction.category_id == category_id)
    
    if date_from:
        date_from_dt = datetime.fromisoformat(date_from)
        query = query.filter(Transaction.created_at >= date_from_dt)
    
    if date_to:
        date_to_dt = datetime.fromisoformat(date_to)
        query = query.filter(Transaction.created_at <= date_to_dt)
    
    if search:
        query = query.filter(Transaction.comment.ilike(f"%{search}%"))
    
    transactions = query.order_by(Transaction.created_at.desc()).offset(offset).limit(limit).all()
    return transactions

@router.put("/{transaction_id}", response_model=TransactionResponse)
def update_transaction(
    transaction_id: int,
    transaction: TransactionUpdate,
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
    
    db_transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == user.id
    ).first()
    
    if not db_transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    update_data = transaction.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_transaction, field, value)
    
    db.commit()
    db.refresh(db_transaction)
    return db_transaction

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
    
    total_income = db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == user.id,
        Transaction.type == TransactionType.INCOME
    ).scalar() or 0
    
    total_expense = db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == user.id,
        Transaction.type == TransactionType.EXPENSE
    ).scalar() or 0
    
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

@router.get("/statistics/monthly", response_model=dict)
def get_monthly_statistics(
    telegram_init_data: str = Header(...),
    db: Session = Depends(get_db),
    month: Optional[int] = Query(None),
    year: Optional[int] = Query(None)
):
    if not validate_telegram_init_data(telegram_init_data):
        raise HTTPException(status_code=401, detail="Invalid Telegram data")
    
    user_info = get_user_from_init_data(telegram_init_data)
    telegram_id = str(user_info['id'])
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    
    if not user:
        return {"months": []}
    
    current_year = year or datetime.now().year
    
    monthly_stats = []
    for m in range(1, 13):
        income = db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == user.id,
            Transaction.type == TransactionType.INCOME,
            extract('month', Transaction.created_at) == m,
            extract('year', Transaction.created_at) == current_year
        ).scalar() or 0
        
        expense = db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == user.id,
            Transaction.type == TransactionType.EXPENSE,
            extract('month', Transaction.created_at) == m,
            extract('year', Transaction.created_at) == current_year
        ).scalar() or 0
        
        monthly_stats.append({
            "month": m,
            "month_name": datetime(current_year, m, 1).strftime("%B"),
            "income": float(income),
            "expense": float(expense),
            "balance": float(income - expense)
        })
    
    return {"months": monthly_stats, "year": current_year}

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