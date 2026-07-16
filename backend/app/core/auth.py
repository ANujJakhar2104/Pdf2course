"""
Verifies the Supabase-issued access token sent by the frontend
(Authorization: Bearer <token>) using the official Supabase Python client.

We delegate verification to supabase.auth.get_user(token) rather than
decoding the JWT ourselves. This works regardless of whether the project
signs tokens with the legacy shared HS256 secret or the newer asymmetric
(ES256/RS256) signing keys — Supabase's SDK handles both transparently.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.supabase_client import supabase

bearer_scheme = HTTPBearer()


class CurrentUser:
    def __init__(self, id: str, email):
        self.id = id
        self.email = email


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> CurrentUser:
    token = credentials.credentials
    try:
        response = supabase.auth.get_user(token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    user = getattr(response, "user", None)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    return CurrentUser(id=user.id, email=user.email)
