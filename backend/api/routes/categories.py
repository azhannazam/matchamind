from fastapi import APIRouter, Depends, HTTPException
from supabase import Client
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/categories", tags=["categories"])

class CategoryCreate(BaseModel):
    name: str
    monthly_limit: Optional[float] = None
    is_indulgence: bool = True

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    monthly_limit: Optional[float] = None
    is_indulgence: Optional[bool] = None

@router.get("/")
async def get_categories(
    user=Depends(get_current_user),
    db: Client = Depends(get_supabase)
):
    """Get all categories for current user"""
    result = db.table('categories')\
        .select('*')\
        .eq('user_id', user['id'])\
        .order('name')\
        .execute()
    
    return result.data

@router.post("/")
async def create_category(
    category: CategoryCreate,
    user=Depends(get_current_user),
    db: Client = Depends(get_supabase)
):
    """Create a new custom category"""
    
    # Check if category already exists
    existing = db.table('categories')\
        .select('id')\
        .eq('user_id', user['id'])\
        .eq('name', category.name)\
        .execute()
    
    if existing.data:
        raise HTTPException(status_code=400, detail="Category already exists")
    
    new_category = {
        'user_id': user['id'],
        'name': category.name,
        'monthly_limit': category.monthly_limit,
        'is_indulgence': category.is_indulgence
    }
    
    result = db.table('categories').insert(new_category).execute()
    return result.data[0]

@router.patch("/{category_id}")
async def update_category(
    category_id: str,
    update: CategoryUpdate,
    user=Depends(get_current_user),
    db: Client = Depends(get_supabase)
):
    """Update a category"""
    
    # Build update dict excluding None values
    update_data = {k: v for k, v in update.dict().items() if v is not None}
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    result = db.table('categories')\
        .update(update_data)\
        .eq('id', category_id)\
        .eq('user_id', user['id'])\
        .execute()
    
    if not result.data:
        raise HTTPException(status_code=404, detail="Category not found")
    
    return result.data[0]

@router.delete("/{category_id}")
async def delete_category(
    category_id: str,
    user=Depends(get_current_user),
    db: Client = Depends(get_supabase)
):
    """Delete a category (transactions will be uncategorized)"""
    
    # First, check if category belongs to user
    category = db.table('categories')\
        .select('id')\
        .eq('id', category_id)\
        .eq('user_id', user['id'])\
        .execute()
    
    if not category.data:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Set transactions with this category to NULL
    db.table('transactions')\
        .update({'category_id': None})\
        .eq('category_id', category_id)\
        .execute()
    
    # Delete category
    db.table('categories')\
        .delete()\
        .eq('id', category_id)\
        .execute()
    
    return {"message": "Category deleted successfully"}

@router.get("/monthly-progress")
async def get_monthly_progress(
    user=Depends(get_current_user),
    db: Client = Depends(get_supabase)
):
    """Check spending progress against monthly limits"""
    
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    # Get categories with limits
    categories = db.table('categories')\
        .select('*')\
        .eq('user_id', user['id'])\
        .is_('monthly_limit', 'neq', None)\
        .execute()
    
    progress = []
    for cat in categories.data:
        # Get this month's spending for this category
        spending = db.table('transactions')\
            .select('amount')\
            .eq('user_id', user['id'])\
            .eq('category_id', cat['id'])\
            .filter('EXTRACT(MONTH FROM transaction_date) = :month', {'month': current_month})\
            .filter('EXTRACT(YEAR FROM transaction_date) = :year', {'year': current_year})\
            .execute()
        
        spent = sum(t['amount'] for t in spending.data)
        limit = cat['monthly_limit']
        
        progress.append({
            'category_id': cat['id'],
            'category_name': cat['name'],
            'spent': round(spent, 2),
            'limit': float(limit),
            'percentage': round((spent / limit * 100), 1) if limit > 0 else 0,
            'remaining': round(limit - spent, 2),
            'is_over_budget': spent > limit
        })
    
    return {"progress": progress}