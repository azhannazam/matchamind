import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from openai import OpenAI
import logging
import json

logger = logging.getLogger(__name__)

class SpendingCoach:
    def __init__(self, openai_client):
        self.client = openai_client
    
    def detect_anomalies(self, transactions: List[Dict], lookback_days: int = 30) -> List[Dict]:
        """Find unusual spending patterns"""
        
        if not transactions:
            return []
        
        try:
            df = pd.DataFrame(transactions)
            
            # Handle date conversion
            if 'transaction_date' in df.columns:
                df['date'] = pd.to_datetime(df['transaction_date'])
            elif 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
            else:
                return []
            
            # Get category name from nested structure or direct
            if 'categories' in df.columns:
                df['category'] = df['categories'].apply(lambda x: x.get('name', 'Uncategorized') if isinstance(x, dict) else 'Uncategorized')
            elif 'category_name' in df.columns:
                df['category'] = df['category_name']
            else:
                df['category'] = 'Uncategorized'
            
            # Calculate weekly spending by category
            df['week'] = df['date'].dt.isocalendar().week
            df['year'] = df['date'].dt.year
            
            weekly_spend = df.groupby(['year', 'week', 'category'])['amount'].sum().reset_index()
            
            if weekly_spend.empty:
                return []
            
            # Get current week
            current_week = weekly_spend['week'].max()
            current_year = weekly_spend[weekly_spend['week'] == current_week]['year'].iloc[0] if not weekly_spend[weekly_spend['week'] == current_week].empty else None
            
            if current_year is None:
                return []
            
            current_spend = weekly_spend[(weekly_spend['week'] == current_week) & (weekly_spend['year'] == current_year)]
            
            anomalies = []
            for _, row in current_spend.iterrows():
                category = row['category']
                current_amount = float(row['amount'])
                
                # Historical average (excluding current week)
                hist_spend = weekly_spend[
                    (weekly_spend['category'] == category) & 
                    ((weekly_spend['week'] < current_week) | (weekly_spend['year'] < current_year))
                ]['amount'].mean()
                
                if pd.notna(hist_spend) and hist_spend > 0 and current_amount > hist_spend * 1.25:
                    increase_pct = ((current_amount - hist_spend) / hist_spend) * 100
                    anomalies.append({
                        'category': category,
                        'current_spend': round(current_amount, 2),
                        'avg_spend': round(hist_spend, 2),
                        'increase_pct': round(increase_pct, 1),
                        'severity': 'warning' if increase_pct > 50 else 'info'
                    })
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Anomaly detection error: {e}")
            return []
    
    def generate_coaching_message(self, anomaly: Dict, user_budget: float) -> str:
        """Generate personalized, actionable advice"""
        
        # Default message in case AI fails
        default_message = f"Your {anomaly['category']} spending is up {anomaly['increase_pct']:.0f}% (RM{anomaly['avg_spend']:.2f} → RM{anomaly['current_spend']:.2f}). Consider reducing by 15% this week to stay on track."
        
        try:
            prompt = f"""
            You are a friendly, non-judgmental financial coach. 
            
            User's spending pattern:
            - Category: {anomaly['category']}
            - This week: RM{anomaly['current_spend']:.2f}
            - Usual weekly: RM{anomaly['avg_spend']:.2f}
            - Increase: {anomaly['increase_pct']:.0f}%
            - Monthly budget: RM{user_budget}
            
            Write a short, encouraging alert (max 40 words) that:
            1. Acknowledges the increase
            2. Suggests ONE specific, actionable alternative
            3. Ties back to their savings goal
            
            Keep it conversational and use emojis.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=100
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Coaching message generation error: {e}")
            return default_message
    
    def check_budget_progress(self, transactions: List[Dict], monthly_budget: float) -> Optional[str]:
        """Check if user is on track to hit budget"""
        
        if not transactions:
            return None
        
        try:
            current_month = datetime.now().month
            
            # Filter this month's transactions
            month_transactions = []
            for t in transactions:
                t_date = t.get('transaction_date') or t.get('date')
                if t_date:
                    if isinstance(t_date, str):
                        t_date = datetime.fromisoformat(t_date)
                    if t_date.month == current_month:
                        month_transactions.append(t)
            
            if not month_transactions:
                return None
            
            month_spend = sum(float(t.get('amount', 0)) for t in month_transactions)
            days_passed = datetime.now().day
            days_in_month = 30
            
            if days_passed == 0:
                return None
                
            projected_spend = (month_spend / days_passed) * days_in_month
            
            if projected_spend > monthly_budget:
                overshoot = projected_spend - monthly_budget
                return f"⚠️ On track to exceed budget by RM{overshoot:.0f} this month. Consider reducing indulgences by 15% this week."
            elif month_spend > monthly_budget * 0.8:
                return f"🎯 You've spent RM{month_spend:.0f} of RM{monthly_budget:.0f} budget ({month_spend/monthly_budget:.0%}). Looking good!"
            
            return None
            
        except Exception as e:
            logger.error(f"Budget progress check error: {e}")
            return None