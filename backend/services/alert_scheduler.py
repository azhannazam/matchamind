from datetime import datetime, timedelta, time
from typing import List, Dict, Optional
import asyncio
import logging
from supabase import Client
from ..ai.coach import SpendingCoach

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AlertScheduler:
    """
    Background scheduler for AI-powered alerts and coaching messages
    """
    
    def __init__(self, db: Client, openai_client, check_interval_minutes: int = 60):
        self.db = db
        self.coach = SpendingCoach(openai_client)
        self.check_interval = check_interval_minutes
        self.is_running = False
    
    async def start(self):
        """Start the alert scheduler background task"""
        self.is_running = True
        logger.info(f"Alert scheduler started (interval: {self.check_interval} minutes)")
        
        while self.is_running:
            try:
                await self.run_checks()
                await asyncio.sleep(self.check_interval * 60)
            except Exception as e:
                logger.error(f"Error in alert scheduler: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
    
    def stop(self):
        """Stop the scheduler"""
        self.is_running = False
        logger.info("Alert scheduler stopped")
    
    async def run_checks(self):
        """Run all alert checks"""
        logger.info("Running scheduled alert checks...")
        
        # Get all active users
        users = self.get_active_users()
        
        for user in users:
            try:
                await self.check_user_alerts(user)
            except Exception as e:
                logger.error(f"Error checking alerts for user {user['id']}: {e}")
    
    def get_active_users(self) -> List[Dict]:
        """Get users active in last 7 days"""
        seven_days_ago = (datetime.now() - timedelta(days=7)).isoformat()
        
        result = self.db.table('profiles')\
            .select('id, email, monthly_budget')\
            .execute()
        
        return result.data
    
    async def check_user_alerts(self, user: Dict):
        """Check all alert conditions for a single user"""
        user_id = user['id']
        
        # Get recent transactions
        transactions = self.get_user_transactions(user_id, days=30)
        
        if not transactions:
            return
        
        # Check for spending anomalies
        anomalies = self.coach.detect_anomalies(transactions)
        
        for anomaly in anomalies:
            await self.create_anomaly_alert(user_id, anomaly, user.get('monthly_budget', 500))
        
        # Check budget progress
        budget_alert = self.check_budget_progress(user_id, transactions, user.get('monthly_budget', 500))
        if budget_alert:
            await self.create_budget_alert(user_id, budget_alert)
        
        # Check spending milestones
        milestone_alert = self.check_milestones(user_id, transactions)
        if milestone_alert:
            await self.create_milestone_alert(user_id, milestone_alert)
        
        # Weekly summary (every Sunday)
        if datetime.now().weekday() == 6:  # Sunday
            await self.create_weekly_summary(user_id, transactions)
    
    def get_user_transactions(self, user_id: str, days: int = 30) -> List[Dict]:
        """Get user transactions for specified period"""
        start_date = (datetime.now() - timedelta(days=days)).date()
        
        result = self.db.table('transactions')\
            .select('*, categories(name, is_indulgence)')\
            .eq('user_id', user_id)\
            .gte('transaction_date', start_date.isoformat())\
            .execute()
        
        return result.data
    
    async def create_anomaly_alert(self, user_id: str, anomaly: Dict, monthly_budget: float):
        """Create an alert for spending anomaly"""
        
        # Check if similar alert was sent in last 7 days
        existing = self.db.table('alerts')\
            .select('id')\
            .eq('user_id', user_id)\
            .eq('type', 'spike')\
            .gte('created_at', (datetime.now() - timedelta(days=7)).isoformat())\
            .execute()
        
        if existing.data:
            return  # Don't spam
        
        # Generate coaching message
        message = self.coach.generate_coaching_message(anomaly, monthly_budget)
        
        # Create alert
        self.db.table('alerts').insert({
            'user_id': user_id,
            'type': 'spike',
            'message': message,
            'severity': anomaly['severity'],
            'metadata': {
                'category': anomaly['category'],
                'current_spend': anomaly['current_spend'],
                'avg_spend': anomaly['avg_spend'],
                'increase_pct': anomaly['increase_pct']
            }
        }).execute()
        
        logger.info(f"Created anomaly alert for user {user_id}: {anomaly['category']}")
    
    def check_budget_progress(self, user_id: str, transactions: List[Dict], monthly_budget: float) -> Optional[Dict]:
        """Check budget progress and return alert if needed"""
        
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        # Filter this month's transactions
        month_transactions = [
            t for t in transactions 
            if datetime.fromisoformat(t['transaction_date']).month == current_month
            and datetime.fromisoformat(t['transaction_date']).year == current_year
        ]
        
        spent = sum(t['amount'] for t in month_transactions)
        
        # Check for 80% threshold
        if spent >= monthly_budget * 0.8 and spent < monthly_budget:
            # Check if alert already sent this month
            existing = self.db.table('alerts')\
                .select('id')\
                .eq('user_id', user_id)\
                .eq('type', 'budget_warning')\
                .gte('created_at', (datetime.now() - timedelta(days=30)).isoformat())\
                .execute()
            
            if not existing.data:
                days_left = 30 - datetime.now().day
                return {
                    'type': 'budget_warning',
                    'spent': spent,
                    'budget': monthly_budget,
                    'percentage': (spent / monthly_budget) * 100,
                    'days_left': days_left,
                    'daily_remaining': (monthly_budget - spent) / days_left if days_left > 0 else 0
                }
        
        return None
    
    def check_milestones(self, user_id: str, transactions: List[Dict]) -> Optional[Dict]:
        """Check for spending/saving milestones"""
        
        # Get all-time total
        all_time = self.db.table('transactions')\
            .select('amount')\
            .eq('user_id', user_id)\
            .execute()
        
        total_spent = sum(t['amount'] for t in all_time.data)
        
        # Milestone thresholds
        milestones = [1000, 5000, 10000, 50000]
        
        for milestone in milestones:
            if total_spent >= milestone:
                # Check if milestone alert already sent
                existing = self.db.table('alerts')\
                    .select('id')\
                    .eq('user_id', user_id)\
                    .eq('type', 'achievement')\
                    .eq('metadata->>milestone', str(milestone))\
                    .execute()
                
                if not existing.data:
                    return {
                        'type': 'achievement',
                        'milestone': milestone,
                        'total_spent': total_spent
                    }
        
        return None
    
    async def create_budget_alert(self, user_id: str, budget_info: Dict):
        """Create budget warning alert"""
        
        message = f"⚠️ You've used {budget_info['percentage']:.0f}% of your monthly budget (RM{budget_info['spent']:.2f} of RM{budget_info['budget']:.2f}). "
        message += f"You have {budget_info['days_left']} days left. "
        message += f"Try to keep daily spending under RM{budget_info['daily_remaining']:.2f} to stay on track!"
        
        self.db.table('alerts').insert({
            'user_id': user_id,
            'type': 'budget_warning',
            'message': message,
            'severity': 'warning',
            'metadata': budget_info
        }).execute()
        
        logger.info(f"Created budget alert for user {user_id}")
    
    async def create_milestone_alert(self, user_id: str, milestone_info: Dict):
        """Create achievement milestone alert"""
        
        message = f"🎉 Amazing milestone! You've tracked RM{milestone_info['total_spent']:,.2f} in total expenses. "
        message += "Every transaction is a step toward better financial awareness. Keep going! 💪"
        
        self.db.table('alerts').insert({
            'user_id': user_id,
            'type': 'achievement',
            'message': message,
            'severity': 'success',
            'metadata': milestone_info
        }).execute()
        
        logger.info(f"Created milestone alert for user {user_id}: RM{milestone_info['milestone']}")
    
    async def create_weekly_summary(self, user_id: str, transactions: List[Dict]):
        """Create weekly summary alert (sent every Sunday)"""
        
        # Get current week's transactions
        today = datetime.now()
        start_of_week = today - timedelta(days=today.weekday() + 1)
        
        week_transactions = [
            t for t in transactions
            if datetime.fromisoformat(t['transaction_date']) >= start_of_week
        ]
        
        if not week_transactions:
            return
        
        total_week = sum(t['amount'] for t in week_transactions)
        total_transactions = len(week_transactions)
        
        # Get top category
        category_spend = {}
        for t in week_transactions:
            cat = t.get('categories', {}).get('name', 'Uncategorized')
            category_spend[cat] = category_spend.get(cat, 0) + t['amount']
        
        top_category = max(category_spend, key=category_spend.get) if category_spend else None
        
        message = f"📊 Weekly Summary: You spent RM{total_week:.2f} across {total_transactions} transactions. "
        if top_category:
            message += f"Top category: {top_category} (RM{category_spend[top_category]:.2f}). "
        
        # Add encouraging message
        if total_week < 300:
            message += "Great week on spending! 🎯"
        elif total_week > 800:
            message += "Higher spending week - review your transactions to see where you can adjust. 💡"
        else:
            message += "You're staying consistent! Keep tracking! 💪"
        
        # Check if already sent this week
        existing = self.db.table('alerts')\
            .select('id')\
            .eq('user_id', user_id)\
            .eq('type', 'achievement')\
            .like('message', 'Weekly Summary%')\
            .gte('created_at', start_of_week.isoformat())\
            .execute()
        
        if not existing.data:
            self.db.table('alerts').insert({
                'user_id': user_id,
                'type': 'achievement',
                'message': message,
                'severity': 'info',
                'metadata': {
                    'week_total': total_week,
                    'transaction_count': total_transactions,
                    'top_category': top_category
                }
            }).execute()
            
            logger.info(f"Created weekly summary for user {user_id}")