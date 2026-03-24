# dependencies.py
"""
Reusable FastAPI dependencies for authentication.
Use get_current_user in any router that needs auth.
"""

from fastapi import HTTPException, Header, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from repositories.auth_repository import get_user_by_token


async def get_current_user(
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    FastAPI dependency — decodes JWT and returns current user dict.
    Use as: user = Depends(get_current_user)
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    token = authorization.replace("Bearer ", "").strip()
    user  = await get_user_by_token(db, token)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return user