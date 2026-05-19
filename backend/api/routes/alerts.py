from fastapi import APIRouter, Depends, HTTPException
from supabase import Client
from typing import List, Dict
from datetime import datetime, timedelta

router = APIRouter(prefix="/alerts", tags=["alerts"])

def get_current_user(user_id: str = "test-user-123"):
    # In production, use Supabase Auth
    return {"id": user_id, "email": f"{user_id}@example.com"}

@router.get("/")
async def get_alerts(
    unread_only: bool = False,
    user=Depends(get_current_user),
    db: Client = Depends(get_supabase)
):
    """Get all alerts for current user"""
    query = db.table('alerts').select('*').eq('user_id', user['id'])
    
    if unread_only:
        query = query.eq('is_read', False)
    
    result = query.order('created_at', desc=True).execute()
    return result.data

@router.patch("/{alert_id}/read")
async def mark_as_read(
    alert_id: str,
    user=Depends(get_current_user),
    db: Client = Depends(get_supabase)
):
    """Mark an alert as read"""
    result = db.table('alerts')\
        .update({'is_read': True, 'read_at': datetime.now().isoformat()})\
        .eq('id', alert_id)\
        .eq('user_id', user['id'])\
        .execute()
    
    if not result.data:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return {"message": "Alert marked as read"}

@router.delete("/{alert_id}")
async def delete_alert(
    alert_id: str,
    user=Depends(get_current_user),
    db: Client = Depends(get_supabase)
):
    """Delete an alert"""
    result = db.table('alerts')\
        .delete()\
        .eq('id', alert_id)\
        .eq('user_id', user['id'])\
        .execute()
    
    if not result.data:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return {"message": "Alert deleted"}

@router.post("/check-now")
async def trigger_alert_check(
    background_tasks: BackgroundTasks,
    user=Depends(get_current_user),
    db: Client = Depends(get_supabase)
):
    """Manually trigger AI alert check"""
    from ai.coach import SpendingCoach
    from openai import OpenAI
    
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    coach = SpendingCoach(openai_client)
    
    # Get recent transactions
    transactions = db.table('transactions')\
        .select('*, categories(name, monthly_limit)')\
        .eq('user_id', user['id'])\
        .gte('transaction_date', date.today() - timedelta(days=30))\
        .execute()
    
    anomalies = coach.detect_anomalies(transactions.data)
    
    alerts_created = []
    for anomaly in anomalies[:3]:  # Limit to 3 alerts per check
        # Check if similar alert exists in last 7 days
        existing = db.table('alerts')\
            .select('id')\
            .eq('user_id', user['id'])\
            .eq('type', 'spike')\
            .gte('created_at', (datetime.now() - timedelta(days=7)).isoformat())\
            .execute()
        
        if not existing.data:
            message = coach.generate_coaching_message(anomaly, 500)
            new_alert = db.table('alerts').insert({
                'user_id': user['id'],
                'type': 'spike',
                'message': message,
                'severity': anomaly['severity'],
                'metadata': anomaly
            }).execute()
            alerts_created.append(new_alert.data[0])
    
    return {
        "message": f"Alert check complete",
        "anomalies_found": len(anomalies),
        "alerts_created": len(alerts_created)
    }