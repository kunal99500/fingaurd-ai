# repositories/auth_repository.py
import os
import random
from datetime import datetime, timedelta
from typing import Optional

from jose import jwt
from passlib.context import CryptContext

# ✅ Read secret from environment — never hardcode in production
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-this-in-production-please")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# In-memory user store
users_db = []

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def generate_otp() -> str:
    return str(random.randint(100000, 999999))


def create_user(email: str, phone: str, password: str, verify_method: str = "email") -> dict:
    """Register a new user. Raises ValueError on duplicate."""
    for u in users_db:
        if email and u.get("email") == email:
            raise ValueError("Email already registered.")
        if phone and u.get("phone") == phone:
            raise ValueError("Phone already registered.")

    password = (password or "").strip()[:72]
    otp = generate_otp()

    user = {
        "user_id": len(users_db) + 1,
        "email": email or "",
        "phone": phone or "",
        "password": pwd_context.hash(password),
        "verified": False,
        "otp": otp,
        "method": verify_method,
    }
    users_db.append(user)
    print(f"📩 OTP for {verify_method} ({email or phone}): {otp}")
    return user


def verify_user(contact: str) -> Optional[dict]:
    """Mark user as verified after OTP check."""
    for user in users_db:
        if user.get("email") == contact or user.get("phone") == contact:
            user["verified"] = True
            user.pop("otp", None)
            return user
    return None


def authenticate_user(email: str = "", phone: str = "", password: str = "") -> Optional[dict]:
    """Authenticate by email or phone + password."""
    for user in users_db:
        contact_match = (
            (email and user.get("email") == email) or
            (phone and user.get("phone") == phone)
        )
        if contact_match and pwd_context.verify(password.strip()[:72], user["password"]):
            return user
    return None


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Generate a signed JWT token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode["exp"] = expire
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT token. Returns payload or None."""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except Exception:
        return None