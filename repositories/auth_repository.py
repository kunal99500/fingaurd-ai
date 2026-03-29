# repositories/auth_repository.py
"""
Multi-user authentication using PostgreSQL.
Every user is stored in the DB — no in-memory lists.
"""
import uuid
import os
import random
from datetime import datetime, timedelta
from typing import Optional
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-this-in-production")
ALGORITHM  = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,
    bcrypt__ident="2b",
)


async def create_user(db: AsyncSession, email: str, phone: str, password: str, verify_method: str = "email") -> dict:
    if email:
        res = await db.execute(text("SELECT id FROM users WHERE email = :e"), {"e": email})
        if res.fetchone():
            raise ValueError("Email already registered.")
    if phone:
        res = await db.execute(text("SELECT id FROM users WHERE phone = :p"), {"p": phone})
        if res.fetchone():
            raise ValueError("Phone already registered.")

    otp       = str(random.randint(100000, 999999))
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
      password = password_bytes[:72].decode('utf-8', errors='ignore')
    hashed_pw = pwd_context.hash(password.strip())

    

    res = await db.execute(text("""
    INSERT INTO users (id, email, phone, password, verified, method, otp, created_at)
    VALUES (:id, :email, :phone, :password, false, :method, :otp, NOW())
    RETURNING id, email, phone, method
"""), {
    "id": str(uuid.uuid4()),
    "email": email or "",
    "phone": phone or "",
    "password": hashed_pw,
    "method": verify_method,
    "otp": otp
})
    await db.commit()
    row = res.fetchone()
    print(f"📩 OTP for {verify_method} ({email or phone}): {otp}")
    return {"user_id": str(row.id), "email": row.email, "phone": row.phone, "otp": otp}


async def verify_user_otp(db: AsyncSession, contact: str, otp: str) -> bool:
    res = await db.execute(
        text("SELECT id, otp FROM users WHERE (email = :c OR phone = :c) AND verified = false"),
        {"c": contact}
    )
    row = res.fetchone()
    if not row or row.otp != otp:
        return False
    await db.execute(text("UPDATE users SET verified = true, otp = null WHERE id = :uid"), {"uid": row.id})
    await db.commit()
    return True


async def authenticate_user(db: AsyncSession, email: str = "", phone: str = "", password: str = "") -> Optional[dict]:
    res = await db.execute(
        text("SELECT id, email, phone, password, verified FROM users WHERE email = :e OR phone = :p LIMIT 1"),
        {"e": email or "", "p": phone or ""}
    )
    row = res.fetchone()
    if not row:
        return None
    if not pwd_context.verify(password.strip()[:72], row.password):
        return None
    if not row.verified:
        return {"error": "not_verified"}
    return {"user_id": str(row.id), "email": row.email, "phone": row.phone}


async def get_user_by_token(db: AsyncSession, token: str) -> Optional[dict]:
    payload = decode_access_token(token)
    if not payload:
        return None
    sub = payload.get("sub")
    res = await db.execute(
        text("SELECT id, email, phone FROM users WHERE email = :s OR phone = :s"),
        {"s": sub}
    )
    row = res.fetchone()
    if not row:
        return None
    return {"user_id": str(row.id), "email": row.email, "phone": row.phone}


async def save_user_gmail(db: AsyncSession, user_id: str, gmail_user: str, gmail_app_password: str):
    await db.execute(text("""
        INSERT INTO user_settings (user_id, gmail_user, gmail_app_password)
        VALUES (:uid, :gu, :gp)
        ON CONFLICT (user_id) DO UPDATE SET gmail_user = :gu, gmail_app_password = :gp
    """), {"uid": user_id, "gu": gmail_user, "gp": gmail_app_password})
    await db.commit()


async def get_user_gmail(db: AsyncSession, user_id: str) -> tuple:
    res = await db.execute(
        text("SELECT gmail_user, gmail_app_password FROM user_settings WHERE user_id = :uid"),
        {"uid": user_id}
    )
    row = res.fetchone()
    return (row.gmail_user or "", row.gmail_app_password or "") if row and row.gmail_user else ("", "")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    to_encode["exp"] = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except Exception:
        return None