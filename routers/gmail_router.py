# routers/gmail_router.py
import os
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from dependencies import get_current_user
from repositories.auth_repository import save_user_gmail, get_user_gmail
from services.gmail_sync import sync_gmail_for_user, run_gmail_sync_loop

router = APIRouter()
_active_syncs: set = set()


class GmailCredentials(BaseModel):
    gmail_user:         str
    gmail_app_password: str


@router.post("/connect")
async def connect_gmail(
    creds: GmailCredentials,
    user: dict = Depends(get_current_user),
    db:   AsyncSession = Depends(get_db)
):
    """Save user's Gmail credentials to their profile."""
    await save_user_gmail(db, user["user_id"], creds.gmail_user, creds.gmail_app_password)
    return {"message": f"Gmail connected: {creds.gmail_user}"}


@router.post("/sync")
async def trigger_sync(
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user),
    db:   AsyncSession = Depends(get_db)
):
    """Trigger Gmail sync for the logged-in user using their own Gmail."""
    user_id = user["user_id"]
    gmail_user, gmail_pass = await get_user_gmail(db, user_id)

    if not gmail_user:
        raise HTTPException(
            status_code=400,
            detail="Gmail not connected. Go to Settings and connect your Gmail first."
        )

    count = await sync_gmail_for_user(user_id, gmail_user, gmail_pass)

    if user_id not in _active_syncs:
        _active_syncs.add(user_id)
        background_tasks.add_task(_auto_sync, user_id, gmail_user, gmail_pass)

    return {"message": f"Sync complete. {count} new transaction(s) found.", "transactions_found": count}


@router.get("/status")
async def sync_status(
    user: dict = Depends(get_current_user),
    db:   AsyncSession = Depends(get_db)
):
    user_id = user["user_id"]
    gmail_user, _ = await get_user_gmail(db, user_id)
    return {
        "gmail_connected":  bool(gmail_user),
        "gmail_user":       gmail_user or "Not connected",
        "auto_sync_active": user_id in _active_syncs,
    }


async def _auto_sync(user_id: str, gmail_user: str, gmail_pass: str):
    try:
        await run_gmail_sync_loop(user_id, gmail_user, gmail_pass, interval_minutes=5)
    finally:
        _active_syncs.discard(user_id)