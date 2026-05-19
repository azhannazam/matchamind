from typing import List, Dict, Optional
from datetime import date, datetime, timedelta
from supabase import Client
import pandas as pd

class ExpenseTracker:
    """Core business logic for expense management"""
    
    def __init__(self, db: Client, user_id: str):
        self.db = db
        self.user_id = user_id
    
    def get_transactions(self, start_date: Optional[date] = None, 
                        end_date: Optional[date] = None,
                        category_id: Optional[str] = None) -> List[Dict]:
        """Get filtered transactions"""
        query = self.db.table('transactions')\
            .select('*, categories(*)')\
            .eq('user_id', self.user_id)
        
        if start_date:
            query = query.gte('transaction_date', start_date.isoformat())
        if end_date:
            query = query.lte('transaction_date', end_date.isoformat())
        if category_id:
            query = query.eq('category_id', category_id)
        
        result = query.order('transaction_date', desc=True).execute()
        return result.data
    
    def get_spending_by_period(self, days: int = 30) -> Dict:
        """Get spending aggregated by time period"""
        start_date = date.today() - timedelta(days=days)
        transactions = self.get_transactions(start_date=start_date)
        
        if not transactions:
            return {"total": 0, "daily_average": 0, "by_day": {}}
        
        df = pd.DataFrame(transactions)
        df['date'] = pd.to_datetime(df['transaction_date'])
        
        daily_spend = df.groupby('date')['amount'].sum().to_dict()
        
        return {
            "total": sum(t['amount'] for t in transactions),
            "daily_average": sum(t['amount'] for t in transactions) / days,
            "by_day": {k.isoformat(): v for k, v in daily_spend.items()}
        }
    
    def get_merchant_insights(self) -> Dict:
        """Get spending patterns by merchant"""
        transactions = self.get_transactions()
        
        if not transactions:
            return {"top_merchants": [], "merchant_count": 0}
        
        df = pd.DataFrame(transactions)
        merchant_stats = df.groupby('merchant').agg({
            'amount': ['sum', 'mean', 'count']
        }).reset_index()
        
        merchant_stats.columns = ['merchant', 'total_spent', 'avg_spent', 'visit_count']
        merchant_stats = merchant_stats.sort_values('total_spent', ascending=False)
        
        return {
            "top_merchants": merchant_stats.head(10).to_dict('records'),
            "merchant_count": len(merchant_stats)
        }
    
    def get_budget_status(self, monthly_budget: float) -> Dict:
        """Check current budget status"""
        today = date.today()
        start_of_month = date(today.year, today.month, 1)
        
        transactions = self.get_transactions(start_date=start_of_month)
        spent_so_far = sum(t['amount'] for t in transactions)
        
        days_passed = today.day
        days_in_month = 30
        projected_spend = (spent_so_far / days_passed) * days_in_month if days_passed > 0 else 0
        
        return {
            "budget": monthly_budget,
            "spent": round(spent_so_far, 2),
            "remaining": round(monthly_budget - spent_so_far, 2),
            "daily_budget_remaining": round((monthly_budget - spent_so_far) / (days_in_month - days_passed), 2) if days_passed < days_in_month else 0,
            "projected_total": round(projected_spend, 2),
            "on_track": projected_spend <= monthly_budget,
            "days_remaining": days_in_month - days_passed
        }
    
    def add_bulk_transactions(self, transactions: List[Dict]) -> List[Dict]:
        """Add multiple transactions at once"""
        for t in transactions:
            t['user_id'] = self.user_id
            t['created_at'] = datetime.now().isoformat()
        
        result = self.db.table('transactions').insert(transactions).execute()
        return result.data