import pytest
import sys
import os

# Add paths
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

@pytest.fixture
def test_user_id():
    """Provide test user ID"""
    return "test-user-123"

@pytest.fixture
def sample_transaction():
    """Provide sample transaction data"""
    return {
        "amount": 45.90,
        "merchant": "Tealive",
        "category": "Matcha/Tea",
        "transaction_date": "2024-01-15",
        "is_indulgence": True
    }

@pytest.fixture
def sample_transactions():
    """Provide multiple sample transactions"""
    return [
        {"amount": 45.90, "merchant": "Tealive", "category": "Matcha/Tea", "date": "2024-01-15"},
        {"amount": 32.40, "merchant": "KFC", "category": "Fried Chicken", "date": "2024-01-16"},
        {"amount": 18.50, "merchant": "Nasi Kandar Pelita", "category": "Mamak", "date": "2024-01-17"},
        {"amount": 120.50, "merchant": "AEON Big", "category": "Groceries", "date": "2024-01-18"}
    ]