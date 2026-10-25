"""
routes_auth.py — Login endpoint that issues JWT tokens.

POST /api/auth/token
  Body: { "username": "transport_officer", "password": "..." }
  Returns: { "access_token": "...", "token_type": "bearer" }

In production, replace the hardcoded credential check with a database User model
and bcrypt password verification (passlib[bcrypt]).
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from backend.app.auth.auth_service import create_access_token
from backend.app.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int
    # Returned explicitly so clients can gate UI on role without decoding the
    # JWT payload themselves (which is fragile and duplicates signing concerns).
    role: str
    name: str


# ---------------------------------------------------------------------------
# PRODUCTION TODO: Replace this hardcoded check with a database User model
# using bcrypt: https://passlib.readthedocs.io/en/stable/lib/passlib.hash.bcrypt.html
# Store users with: INSERT INTO users (username, hashed_password, role) VALUES (...)
# ---------------------------------------------------------------------------
_STATIC_CREDENTIALS = {
    "transport_officer": {
        "password_env_var": "TRANSPORT_OFFICER_PASSWORD",  # Must be set in .env
        "role": "transport_officer",
        "name": "VSB Transport Officer",
    },
    "admin": {
        "password_env_var": "ADMIN_PASSWORD",
        "role": "admin",
        "name": "System Administrator",
    },
}


@router.post("/token", response_model=TokenResponse)
def login(payload: LoginRequest):
    """
    Issues a signed JWT token for authenticated transport officers and admins.
    Tokens expire after JWT_ACCESS_TOKEN_EXPIRE_MINUTES (default: 480 = 8 hours).
    """
    import os

    user = _STATIC_CREDENTIALS.get(payload.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    expected_password = (
        getattr(settings, user["password_env_var"], None)
        or os.environ.get(user["password_env_var"], "")
    )
    import hmac
    if not expected_password or not hmac.compare_digest(payload.password, expected_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(
        {
            "sub": payload.username,
            "role": user["role"],
            "name": user["name"],
        }
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in_minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
        role=user["role"],
        name=user["name"],
    )
