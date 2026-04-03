# routers/family_router.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional
from database import get_db
from dependencies import get_current_user
from services.family_service import (
    send_link_request,
    accept_link_request,
    get_family_link,
    get_parent_dashboard,
    get_parent_notifications,
    request_emergency_otp,
    verify_emergency_otp,
)

router = APIRouter(prefix="", tags=["Family"])


class LinkRequest(BaseModel):
    parent_email: str


class EmergencyOTPRequest(BaseModel):
    amount: float
    reason: str


class VerifyOTPRequest(BaseModel):
    otp: str
    amount: float


class AcceptLinkRequest(BaseModel):
    student_id: str


@router.post("/link/request")
async def request_parent_link(
    body: LinkRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Student sends link request to parent."""
    result = await send_link_request(db, user["user_id"], body.parent_email)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/link/accept")
async def accept_parent_link(
    body: AcceptLinkRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Parent accepts student's link request."""
    result = await accept_link_request(db, user["user_id"], body.student_id)
    return result


@router.get("/link/status")
async def get_link_status(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get family link status for current user."""
    return await get_family_link(db, user["user_id"])


@router.get("/parent/dashboard")
async def parent_dashboard(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Parent gets full dashboard of student spending."""
    return await get_parent_dashboard(db, user["user_id"])


@router.get("/parent/notifications")
async def parent_notifications(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Parent gets all notifications."""
    return await get_parent_notifications(db, user["user_id"])


@router.post("/emergency/request")
async def emergency_otp_request(
    body: EmergencyOTPRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Student requests emergency OTP from parent."""
    result = await request_emergency_otp(
        db, user["user_id"], body.amount, body.reason
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/emergency/verify")
async def emergency_otp_verify(
    body: VerifyOTPRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Student verifies emergency OTP."""
    result = await verify_emergency_otp(
        db, user["user_id"], body.otp, body.amount
    )
    if not result["valid"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result
