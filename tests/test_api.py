import pytest
from fastapi.testclient import TestClient
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

from main import app

client = TestClient(app)

class TestAPI:
    """Test API endpoints"""
    
    def test_health_check(self):
        """Test health endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    def test_root_endpoint(self):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        assert "MatchaMind" in response.json()["message"]
    
    def test_get_categories(self):
        """Test categories endpoint"""
        response = client.get("/categories/", headers={"X-User-ID": "test-user-123"})
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_create_transaction(self):
        """Test transaction creation"""
        transaction_data = {
            "amount": 25.50,
            "merchant": "Test Cafe",
            "transaction_date": "2024-01-15",
            "notes": "Test transaction"
        }
        response = client.post("/transactions/", 
                              json=transaction_data,
                              headers={"X-User-ID": "test-user-123"})
        assert response.status_code == 200
        assert response.json()["success"] == True
    
    def test_get_transactions(self):
        """Test getting transactions"""
        response = client.get("/transactions/recent?days=30", 
                             headers={"X-User-ID": "test-user-123"})
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_parse_transaction(self):
        """Test AI parsing endpoint"""
        parse_data = {
            "raw_text": "RM 45.90 - Tealive (Matcha Latte)",
            "transaction_date": "2024-01-15"
        }
        response = client.post("/transactions/parse-and-add",
                              json=parse_data,
                              headers={"X-User-ID": "test-user-123"})
        # Should work or return error if no OpenAI key
        assert response.status_code in [200, 422, 500]
    
    def test_get_alerts(self):
        """Test alerts endpoint"""
        response = client.get("/alerts/", headers={"X-User-ID": "test-user-123"})
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_get_analytics_summary(self):
        """Test analytics summary"""
        response = client.get("/analytics/summary?days=30",
                             headers={"X-User-ID": "test-user-123"})
        assert response.status_code == 200
        data = response.json()
        assert "total_spent" in data
        assert "total_transactions" in data

class TestErrorHandling:
    """Test error handling"""
    
    def test_invalid_transaction(self):
        """Test invalid transaction data"""
        invalid_data = {
            "amount": -10,  # Negative amount
            "merchant": ""
        }
        response = client.post("/transactions/",
                              json=invalid_data,
                              headers={"X-User-ID": "test-user-123"})
        assert response.status_code == 422  # Validation error
    
    def test_nonexistent_transaction(self):
        """Test deleting non-existent transaction"""
        response = client.delete("/transactions/nonexistent-id",
                                headers={"X-User-ID": "test-user-123"})
        assert response.status_code == 404
    
    def test_empty_parse(self):
        """Test parsing empty text"""
        parse_data = {"raw_text": ""}
        response = client.post("/transactions/parse-and-add",
                              json=parse_data,
                              headers={"X-User-ID": "test-user-123"})
        assert response.status_code == 422

if __name__ == "__main__":
    pytest.main([__file__, "-v"])