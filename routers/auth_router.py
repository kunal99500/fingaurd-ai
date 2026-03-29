# routers/auth_router.py
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from repositories.auth_repository import (
    create_user, verify_user_otp, authenticate_user, create_access_token
)
from utils.otp_utils import send_otp

router = APIRouter(prefix="/auth", tags=["Authentication"])


class SignupRequest(BaseModel):
    email:    Optional[str] = ""
    phone:    Optional[str] = ""
    password: str
    method:   str


class VerifyOTPRequest(BaseModel):
    contact: str
    otp:     str


class LoginRequest(BaseModel):
    email:    Optional[str] = ""
    phone:    Optional[str] = ""
    password: str


@router.post("/signup")
async def signup(req: SignupRequest, db: AsyncSession = Depends(get_db)):
    if req.method.lower() not in ["email", "phone"]:
        raise HTTPException(status_code=400, detail="method must be 'email' or 'phone'")
    try:
        user = await create_user(db, req.email, req.phone, req.password, req.method.lower())
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

    contact = req.email if req.method.lower() == "email" else req.phone
    send_otp(contact)
    return {
        "message": f"OTP sent to your {req.method}. Please verify.",
        "user_id": user["user_id"],
        "otp": user["otp"]  # ← show OTP in response for testing
    }


@router.post("/verify-otp")
async def verify(req: VerifyOTPRequest, db: AsyncSession = Depends(get_db)):
    ok = await verify_user_otp(db, req.contact, req.otp)
    if not ok:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP.")
    return {"message": "Verified! You can now log in."}


@router.post("/login")
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await authenticate_user(db, email=req.email or "", phone=req.phone or "", password=req.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if user.get("error") == "not_verified":
        raise HTTPException(status_code=403, detail="Account not verified. Check your OTP.")
    token = create_access_token({"sub": user["email"] or user["phone"]})
    return {"access_token": token, "token_type": "bearer", "user_id": user["user_id"]}