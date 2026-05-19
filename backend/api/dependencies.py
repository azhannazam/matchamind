from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client, Client
import os
from typing import Optional

security = HTTPBearer()

def get_supabase() -> Client:
    """Get Supabase client instance"""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        raise HTTPException(status_code=500, detail="Supabase configuration missing")
    return create_client(url, key)

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Client = Depends(get_supabase)
):
    """
    Get current authenticated user.
    For demo, returns a test user. In production, validate JWT token.
    """
    # Demo mode - return test user
    if os.getenv("DEMO_MODE", "true").lower() == "true":
        return {"id": "test-user-123", "email": "demo@matchamind.com"}
    
    # Production - validate JWT
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    token = credentials.credentials
    try:
        # Verify JWT with Supabase
        user = db.auth.get_user(token)
        return user.user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )