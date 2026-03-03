from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models import TransactionType

class TransactionCreate(BaseModel):
    amount: float = Field(..., gt=0)
    type: TransactionType
    category_id: int
    comment: Optional[str] = None

class TransactionResponse(BaseModel):
    id: int
    amount: float
    type: TransactionType
    category_id: int
    comment: Optional[str]
    created_at: datetime
    class Config:
        from_attributes = True

class CategoryCreate(BaseModel):
    name: str
    icon: str = "💰"

class CategoryResponse(BaseModel):
    id: int
    name: str
    icon: str
    class Config:
        from_attributes = True