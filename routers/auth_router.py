# routers/auth_router.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from repositories.auth_repository import (
    create_user,
    authenticate_user,
    create_access_token,
    verify_user,
)
from utils.otp_utils import send_otp, verify_otp, resend_otp

router = APIRouter(prefix="/auth", tags=["Authentication"])


class SignupRequest(BaseModel):
    email: Optional[str] = ""
    phone: Optional[str] = ""
    password: str
    method: str  # "email" or "phone"


class VerifyOTPRequest(BaseModel):
    contact: str
    otp: str


class LoginRequest(BaseModel):
    email: Optional[str] = ""
    phone: Optional[str] = ""
    password: str


@router.post("/signup")
def signup(req: SignupRequest):
    verify_method = req.method.lower()
    if verify_method not in ["email", "phone"]:
        raise HTTPException(status_code=400, detail="method must be 'email' or 'phone'")

    try:
        user = create_user(req.email, req.phone, req.password, verify_method)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

    contact = req.email if verify_method == "email" else req.phone
    send_otp(contact)

    return {
        "message": f"OTP sent to your {verify_method}. Please verify to activate your account.",
        "user_id": user["user_id"],
    }


@router.post("/verify-otp")
def verify(req: VerifyOTPRequest):
    if not verify_otp(req.contact, req.otp):
        raise HTTPException(status_code=400, detail="Invalid or expired OTP.")
    user = verify_user(req.contact)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "OTP verified successfully! You can now log in."}


@router.post("/resend-otp")
def resend(contact: str):
    return resend_otp(contact)


@router.post("/login")
def login(req: LoginRequest):
    user = authenticate_user(
        email=req.email or "",
        phone=req.phone or "",
        password=req.password
    )
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user["verified"]:
        raise HTTPException(status_code=403, detail="Account not verified. Check your OTP.")

    token = create_access_token({"sub": user["email"] or user["phone"]})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user["user_id"],
    }