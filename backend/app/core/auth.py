from typing import Optional
import os
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client, Client

from app.core.config import settings

bearer_scheme = HTTPBearer()

# Settings se URL aur Anon Key utha rahe hain (fallback os.getenv pe hai)
SUPABASE_URL = getattr(settings, "supabase_url", os.getenv("SUPABASE_URL"))
SUPABASE_ANON_KEY = getattr(settings, "supabase_anon_key", os.getenv("SUPABASE_ANON_KEY"))

# Supabase Client Initialize
supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

class CurrentUser:
    def __init__(self, id: str, email: Optional[str]):
        self.id = id
        self.email = email

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> CurrentUser:
    token = credentials.credentials
    try:
        # Seedha Supabase API se token verify karwa rahe hain
        user_response = supabase.auth.get_user(token)
        
        if not user_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )
            
        return CurrentUser(
            id=user_response.user.id, 
            email=user_response.user.email
        )
    except Exception as e:
        print(f"Supabase Auth Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )