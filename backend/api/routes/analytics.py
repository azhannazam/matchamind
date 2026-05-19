from fastapi import APIRouter, Depends, HTTPException
from supabase import Client
from typing import List, Dict, Optional
from datetime import datetime, timedelta, date
import pandas as pd
import json

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/summary")
async def get_summary(
    days: int = 30,
    user=Depends(get_current_user),
    db: Client = Depends(get_supabase)
):
    """Get high-level spending summary"""
    
    start_date = date.today() - timedelta(days=days)
    
    # Get transactions with categories
    transactions = db.table('transactions')\
        .select('*, categories(name, is_indulgence)')\
        .eq('user_id', user['id'])\
        .gte('transaction_date', start_date.isoformat())\
        .execute()
    
    df = pd.DataFrame(transactions.data)
    
    if df.empty:
        return {
            "total_spent": 0,
            "total_transactions": 0,
            "avg_transaction": 0,
            "indulgence_spent": 0,
            "essential_spent": 0,
            "top_category": None,
            "top_merchant": None,
            "daily_avg": 0
        }
    
    # Calculate metrics
    total_spent = df['amount'].sum()
    total_transactions = len(df)
    avg_transaction = df['amount'].mean()
    
    # Indulgence vs essential
    df['is_indulgence'] = df['categories'].apply(lambda x: x.get('is_indulgence', True))
    indulgence_spent = df[df['is_indulgence']]['amount'].sum()
    essential_spent = total_spent - indulgence_spent
    
    # Top category
    df['category_name'] = df['categories'].apply(lambda x: x.get('name', 'Uncategorized'))
    top_category = df.groupby('category_name')['amount'].sum().idxmax() if not df.empty else None
    
    # Top merchant
    top_merchant = df.groupby('merchant')['amount'].sum().idxmax() if not df.empty else None
    
    # Daily average
    unique_days = df['transaction_date'].nunique()
    daily_avg = total_spent / unique_days if unique_days > 0 else 0
    
    return {
        "total_spent": round(total_spent, 2),
        "total_transactions": total_transactions,
        "avg_transaction": round(avg_transaction, 2),
        "indulgence_spent": round(indulgence_spent, 2),
        "essential_spent": round(essential_spent, 2),
        "indulgence_percentage": round((indulgence_spent / total_spent * 100), 1) if total_spent > 0 else 0,
        "top_category": top_category,
        "top_merchant": top_merchant,
        "daily_avg": round(daily_avg, 2)
    }

@router.get("/category-breakdown")
async def get_category_breakdown(
    days: int = 30,
    user=Depends(get_current_user),
    db: Client = Depends(get_supabase)
):
    """Get spending breakdown by category"""
    
    start_date = date.today() - timedelta(days=days)
    
    result = db.table('transactions')\
        .select('amount, categories(name)')\
        .eq('user_id', user['id'])\
        .gte('transaction_date', start_date.isoformat())\
        .execute()
    
    df = pd.DataFrame(result.data)
    
    if df.empty:
        return {"categories": []}
    
    df['category'] = df['categories'].apply(lambda x: x.get('name', 'Uncategorized'))
    breakdown = df.groupby('category')['amount'].agg(['sum', 'count']).reset_index()
    breakdown.columns = ['category', 'total', 'transaction_count']
    breakdown['percentage'] = (breakdown['total'] / breakdown['total'].sum() * 100).round(1)
    
    return {"categories": breakdown.to_dict('records')}

@router.get("/trends")
async def get_spending_trends(
    days: int = 90,
    user=Depends(get_current_user),
    db: Client = Depends(get_supabase)
):
    """Get daily spending trends"""
    
    start_date = date.today() - timedelta(days=days)
    
    result = db.table('transactions')\
        .select('amount, transaction_date, categories(name, is_indulgence)')\
        .eq('user_id', user['id'])\
        .gte('transaction_date', start_date.isoformat())\
        .execute()
    
    df = pd.DataFrame(result.data)
    
    if df.empty:
        return {"daily_data": [], "weekly_averages": []}
    
    # Daily aggregation
    df['date'] = pd.to_datetime(df['transaction_date'])
    daily = df.groupby('date')['amount'].sum().reset_index()
    daily['rolling_7d'] = daily['amount'].rolling(window=7).mean()
    
    # Weekly averages by category
    df['week'] = df['date'].dt.isocalendar().week
    df['category'] = df['categories'].apply(lambda x: x.get('name', 'Uncategorized'))
    weekly_avg = df.groupby(['week', 'category'])['amount'].mean().reset_index()
    
    return {
        "daily_data": daily.to_dict('records'),
        "weekly_averages": weekly_avg.to_dict('records')
    }

@router.get("/comparison")
async def get_comparison(
    period1_days: int = 30,
    period2_days: int = 30,
    period2_offset_days: int = 30,
    user=Depends(get_current_user),
    db: Client = Depends(get_supabase)
):
    """Compare two time periods (e.g., this month vs last month)"""
    
    period1_start = date.today() - timedelta(days=period1_days)
    period2_start = date.today() - timedelta(days=period1_days + period2_offset_days)
    period2_end = period2_start + timedelta(days=period2_days)
    
    # Get period 1 data
    p1_result = db.table('transactions')\
        .select('amount, categories(name)')\
        .eq('user_id', user['id'])\
        .gte('transaction_date', period1_start.isoformat())\
        .execute()
    
    # Get period 2 data
    p2_result = db.table('transactions')\
        .select('amount, categories(name)')\
        .eq('user_id', user['id'])\
        .gte('transaction_date', period2_start.isoformat())\
        .lt('transaction_date', period2_end.isoformat())\
        .execute()
    
    p1_total = sum(t['amount'] for t in p1_result.data)
    p2_total = sum(t['amount'] for t in p2_result.data)
    
    change_pct = ((p1_total - p2_total) / p2_total * 100) if p2_total > 0 else 0
    
    return {
        "period1": {
            "label": f"Last {period1_days} days",
            "total": round(p1_total, 2),
            "transaction_count": len(p1_result.data)
        },
        "period2": {
            "label": f"Previous {period2_days} days",
            "total": round(p2_total, 2),
            "transaction_count": len(p2_result.data)
        },
        "change_percentage": round(change_pct, 1),
        "trend": "up" if change_pct > 0 else "down"
    }