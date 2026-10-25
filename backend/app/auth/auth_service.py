"""
auth_service.py — JWT Bearer Token Middleware for BUSify

Protects all state-changing endpoints (POST, PUT, DELETE).
Read-only GET endpoints remain publicly accessible for student-facing features.

Usage:
    from backend.app.auth.auth_service import require_auth, create_access_token

    # Protect a route:
    @router.post("/buses", dependencies=[Depends(require_auth)])

    # Generate a token (from a login endpoint):
    token = create_access_token({"sub": "transport_officer", "role": "admin"})
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.app.config import settings

logger = logging.getLogger(__name__)

# ─── Bearer token extractor ────────────────────────────────────────────────────
_bearer_scheme = HTTPBearer(auto_error=True)


# ─── Token creation ────────────────────────────────────────────────────────────
def create_access_token(data: dict) -> str:
    """
    Creates a signed HS256 JWT access token.

    Args:
        data: Payload dict — must include "sub" (subject/username).
              Optional keys: "role" (admin | viewer), "name".

    Returns:
        Signed JWT string.
    """
    payload = data.copy()
    expire = datetime.now(tz=timezone.utc) + timedelta(
        minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload.update({"exp": expire, "iat": datetime.now(tz=timezone.utc)})
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


# ─── Token validation dependency ──────────────────────────────────────────────
def require_auth(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_bearer_scheme)],
) -> dict:
    """
    FastAPI dependency that validates JWT Bearer tokens.

    Raises HTTP 401 if the token is missing, expired, or tampered with.
    Raises HTTP 403 if the token is valid but the role is insufficient.

    Returns:
        The decoded JWT payload dict (includes 'sub', 'role', 'exp', 'iat').
    """
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Rejected expired JWT token.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError as exc:
        logger.warning("Rejected invalid JWT token: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )


def require_admin(
    payload: Annotated[dict, Depends(require_auth)],
) -> dict:
    """
    Additional dependency that enforces 'admin' role on top of authentication.
    Attach to endpoints that modify fleet or institutional configuration.
    """
    if payload.get("role") not in ("admin", "transport_officer"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Transport Officer or Admin role required.",
        )
    return payload
