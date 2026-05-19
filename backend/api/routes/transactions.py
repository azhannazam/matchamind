from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from supabase import Client
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import date, datetime, timedelta
import os
import logging
from openai import OpenAI

from ..dependencies import get_supabase, get_current_user
from ...ai.parser import TransactionParser
from ...ai.coach import SpendingCoach

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/transactions", tags=["transactions"])

class TransactionCreate(BaseModel):
    amount: float
    merchant: str
    transaction_date: Optional[date] = None
    notes: Optional[str] = None
    category_id: Optional[str] = None

class TransactionParseRequest(BaseModel):
    raw_text: str
    transaction_date: Optional[date] = None

@router.get("/recent")
async def get_recent_transactions(
    days: int = 30,
    limit: int = 100,
    user: Dict = Depends(get_current_user),
    db: Client = Depends(get_supabase)
):
    """Get recent transactions for the user"""
    start_date = date.today() - timedelta(days=days)
    
    result = db.table('transactions')\
        .select('*, categories(name, is_indulgence)')\
        .eq('user_id', user['id'])\
        .gte('transaction_date', start_date.isoformat())\
        .order('transaction_date', desc=True)\
        .limit(limit)\
        .execute()
    
    # Transform data for frontend
    transactions = []
    for t in result.data:
        transactions.append({
            'id': t['id'],
            'amount': float(t['amount']),
            'merchant': t['merchant'],
            'category_name': t['categories']['name'] if t.get('categories') else 'Uncategorized',
            'is_indulgence': t['categories']['is_indulgence'] if t.get('categories') else False,
            'transaction_date': t['transaction_date'],
            'notes': t.get('notes', ''),
            'created_at': t['created_at']
        })
    
    return transactions

@router.post("/")
async def create_transaction(
    transaction: TransactionCreate,
    user: Dict = Depends(get_current_user),
    db: Client = Depends(get_supabase)
):
    """Create a new transaction manually"""
    
    new_transaction = {
        'user_id': user['id'],
        'amount': transaction.amount,
        'merchant': transaction.merchant,
        'transaction_date': transaction.transaction_date or date.today(),
        'notes': transaction.notes,
        'category_id': transaction.category_id,
        'parsed_by_ai': False,
        'created_at': datetime.now().isoformat()
    }
    
    result = db.table('transactions').insert(new_transaction).execute()
    
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create transaction")
    
    return {"success": True, "transaction": result.data[0]}

@router.post("/parse-and-add")
async def parse_and_add_transaction(
    request: TransactionParseRequest,
    background_tasks: BackgroundTasks,
    user: Dict = Depends(get_current_user),
    db: Client = Depends(get_supabase)
):
    """Parse raw text and add transaction"""
    
    # Get user's categories
    categories_result = db.table('categories')\
        .select('name')\
        .eq('user_id', user['id'])\
        .execute()
    
    category_names = [c['name'] for c in categories_result.data] if categories_result.data else []
    if not category_names:
        # Default categories if none exist
        category_names = ['Matcha/Tea', 'Mamak', 'Fried Chicken', 'Coffee', 'Groceries', 'Essentials', 'Dining Out']
    
    # AI parsing
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")
    
    parser = TransactionParser(api_key=openai_api_key)
    
    try:
        parsed = parser.parse_raw_text(request.raw_text, category_names)
    except Exception as e:
        logger.error(f"AI parsing failed: {e}")
        raise HTTPException(status_code=422, detail=f"Could not parse text: {str(e)}")
    
    # Find or create category
    category_result = db.table('categories')\
        .select('id')\
        .eq('user_id', user['id'])\
        .eq('name', parsed.category)\
        .execute()
    
    category_id = None
    if category_result.data:
        category_id = category_result.data[0]['id']
    else:
        # Create category if it doesn't exist
        new_category = db.table('categories').insert({
            'user_id': user['id'],
            'name': parsed.category,
            'is_indulgence': parsed.is_indulgence
        }).execute()
        if new_category.data:
            category_id = new_category.data[0]['id']
    
    # Save transaction
    new_transaction = {
        'user_id': user['id'],
        'amount': parsed.amount,
        'merchant': parsed.merchant,
        'category_id': category_id,
        'raw_text': request.raw_text,
        'parsed_by_ai': True,
        'transaction_date': request.transaction_date or date.today(),
        'created_at': datetime.now().isoformat()
    }
    
    result = db.table('transactions').insert(new_transaction).execute()
    
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to save transaction")
    
    # Trigger alert check in background (optional, can be re-enabled)
    # background_tasks.add_task(check_for_alerts, user['id'], db)
    
    return {
        "success": True,
        "message": "Transaction added successfully",
        "parsed_data": {
            "amount": parsed.amount,
            "merchant": parsed.merchant,
            "category": parsed.category,
            "confidence": parsed.confidence,
            "is_indulgence": parsed.is_indulgence
        },
        "transaction_id": result.data[0]['id']
    }

@router.delete("/{transaction_id}")
async def delete_transaction(
    transaction_id: str,
    user: Dict = Depends(get_current_user),
    db: Client = Depends(get_supabase)
):
    """Delete a transaction"""
    
    result = db.table('transactions')\
        .delete()\
        .eq('id', transaction_id)\
        .eq('user_id', user['id'])\
        .execute()
    
    if not result.data:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    return {"success": True, "message": "Transaction deleted"}

@router.get("/export")
async def export_transactions(
    user: Dict = Depends(get_current_user),
    db: Client = Depends(get_supabase)
):
    """Export all user transactions as CSV data"""
    
    result = db.table('transactions')\
        .select('*, categories(name)')\
        .eq('user_id', user['id'])\
        .order('transaction_date', desc=True)\
        .execute()
    
    return {"success": True, "transactions": result.data}