from pydantic import BaseModel, Field, validator
from datetime import date, datetime
from typing import Optional, List
from decimal import Decimal

# ============ Transaction Models ============
class TransactionBase(BaseModel):
    amount: float = Field(..., gt=0, description="Transaction amount in RM")
    merchant: str = Field(..., min_length=1, max_length=100)
    transaction_date: Optional[date] = None
    notes: Optional[str] = None

class TransactionCreate(TransactionBase):
    raw_text: Optional[str] = None
    category_id: Optional[str] = None

class TransactionParseRequest(BaseModel):
    raw_text: str
    transaction_date: Optional[date] = None

class TransactionParseResponse(BaseModel):
    amount: float
    merchant: str
    category: str
    confidence: float
    is_indulgence: bool
    raw_text: str

class TransactionResponse(TransactionBase):
    id: str
    user_id: str
    category_id: Optional[str]
    category_name: Optional[str]
    is_indulgence: Optional[bool]
    raw_text: Optional[str]
    parsed_by_ai: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# ============ Category Models ============
class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    monthly_limit: Optional[float] = Field(None, gt=0)
    is_indulgence: bool = True
    color: Optional[str] = "#808080"
    icon: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    monthly_limit: Optional[float] = None
    is_indulgence: Optional[bool] = None
    color: Optional[str] = None
    icon: Optional[str] = None

class CategoryResponse(CategoryBase):
    id: str
    user_id: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# ============ Alert Models ============
class AlertBase(BaseModel):
    type: str = Field(..., pattern="^(spike|budget_warning|savings_milestone|achievement)$")
    message: str
    severity: str = Field(..., pattern="^(info|warning|critical|success)$")
    metadata: Optional[dict] = None

class AlertCreate(AlertBase):
    pass

class AlertResponse(AlertBase):
    id: str
    user_id: str
    is_read: bool
    read_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True

class AlertUpdate(BaseModel):
    is_read: Optional[bool] = None

# ============ Analytics Models ============
class SpendingSummary(BaseModel):
    total_spent: float
    total_transactions: int
    avg_transaction: float
    indulgence_spent: float
    essential_spent: float
    indulgence_percentage: float
    top_category: Optional[str]
    top_merchant: Optional[str]
    daily_avg: float

class CategoryBreakdown(BaseModel):
    category: str
    total: float
    transaction_count: int
    percentage: float

class TrendData(BaseModel):
    date: str
    amount: float
    rolling_7d: Optional[float]

class PeriodComparison(BaseModel):
    period1: dict
    period2: dict
    change_percentage: float
    trend: str  # 'up' or 'down'

class BudgetProgress(BaseModel):
    budget: float
    spent: float
    remaining: float
    daily_budget_remaining: float
    projected_total: float
    on_track: bool
    days_remaining: int

# ============ User Models ============
class UserProfile(BaseModel):
    id: str
    email: str
    full_name: Optional[str]
    monthly_budget: float = 500.00
    savings_goal: float = 1000.00
    currency: str = "MYR"
    notification_enabled: bool = True
    created_at: datetime
    updated_at: datetime

class UserProfileUpdate(BaseModel):
    full_name: Optional[str]
    monthly_budget: Optional[float] = Field(None, gt=0)
    savings_goal: Optional[float] = Field(None, ge=0)
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    notification_enabled: Optional[bool]

# ============ AI Models ============
class ParsedTransaction(BaseModel):
    amount: float
    merchant: str
    category: str
    confidence: float
    is_indulgence: bool

class CoachingMessage(BaseModel):
    type: str  # 'anomaly', 'budget', 'milestone', 'tip'
    message: str
    severity: str
    action_suggestion: Optional[str]

class AnomalyDetection(BaseModel):
    category: str
    current_spend: float
    avg_spend: float
    increase_pct: float
    severity: str

# ============ Request/Response Wrappers ============
class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None
    error: Optional[str] = None

class PaginatedResponse(BaseModel):
    items: List[dict]
    total: int
    page: int
    page_size: int
    has_next: bool

# ============ Validators ============
def validate_amount(cls, v):
    if v <= 0:
        raise ValueError("Amount must be greater than 0")
    if v > 10000:
        raise ValueError("Amount seems too high. Please verify")
    return v

def validate_date_not_future(cls, v):
    if v and v > date.today():
        raise ValueError("Transaction date cannot be in the future")
    return v