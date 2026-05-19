import streamlit as st
from datetime import datetime, date
import pandas as pd
import re

def format_currency(amount: float) -> str:
    """Format amount as Malaysian Ringgit"""
    return f"RM {amount:,.2f}"

def extract_merchant_from_text(text: str) -> str:
    """Simple regex to extract merchant names from text"""
    # Remove common prefixes
    text = re.sub(r'^(paid|spent|rm|myr)\s+', '', text.lower())
    
    # Look for common patterns
    patterns = [
        r'at\s+([a-z\s]+?)(?:\s+for|\s+\(|$)',
        r'from\s+([a-z\s]+?)(?:\s+\(|$)',
        r'^([a-z\s]+?)(?:\s+-\s+|\s+\(|$)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            merchant = match.group(1).strip().title()
            if len(merchant) > 2:
                return merchant
    
    return "Unknown Merchant"

def get_emoji_for_category(category: str) -> str:
    """Return emoji for common categories"""
    emoji_map = {
        'matcha': '🍵', 'tea': '🍵',
        'coffee': '☕',
        'mamak': '🍛',
        'fried chicken': '🍗', 'kfc': '🍗',
        'groceries': '🛒',
        'essentials': '💡',
        'dining': '🍽️',
        'transport': '🚗',
        'shopping': '🛍️'
    }
    
    category_lower = category.lower()
    for key, emoji in emoji_map.items():
        if key in category_lower:
            return emoji
    
    return '💰'

def get_severity_color(severity: str) -> str:
    """Return color for alert severity"""
    colors = {
        'info': 'blue',
        'warning': 'orange',
        'critical': 'red',
        'success': 'green'
    }
    return colors.get(severity, 'gray')

def validate_transaction_input(amount: float, merchant: str) -> tuple[bool, str]:
    """Validate transaction input"""
    if amount <= 0:
        return False, "Amount must be greater than 0"
    if amount > 10000:
        return False, "Amount seems too high. Please verify."
    if not merchant or len(merchant.strip()) < 2:
        return False, "Please enter a valid merchant name"
    return True, ""

def cache_with_ttl(ttl_seconds: int = 300):
    """Decorator for caching API responses"""
    def decorator(func):
        cache_key = f"cache_{func.__name__}"
        
        def wrapper(*args, **kwargs):
            # Check if cached data exists and is fresh
            if cache_key in st.session_state:
                cached_time, cached_data = st.session_state[cache_key]
                if (datetime.now() - cached_time).seconds < ttl_seconds:
                    return cached_data
            
            # Get fresh data
            result = func(*args, **kwargs)
            st.session_state[cache_key] = (datetime.now(), result)
            return result
        
        return wrapper
    return decorator

def generate_share_text(transactions_df: pd.DataFrame, total_spent: float) -> str:
    """Generate text for sharing progress"""
    if transactions_df.empty:
        return "I'm using MatchaMind to track my spending! 🍵"
    
    top_category = transactions_df.groupby('category')['amount'].sum().idxmax() if not transactions_df.empty else None
    days_tracked = transactions_df['date'].nunique()
    
    share_text = f"I've tracked {len(transactions_df)} transactions over {days_tracked} days with MatchaMind! "
    share_text += f"Total spent: RM{total_spent:.2f}. "
    if top_category:
        share_text += f"Top category: {top_category}. "
    share_text += "Track your spending smarter at MatchaMind! 🍵"
    
    return share_text