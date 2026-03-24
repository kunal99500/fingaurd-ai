# models.py
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Boolean, DateTime, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database import Base


def gen_uuid():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"
    id         = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    email      = Column(String(255), unique=True, nullable=True, index=True)
    phone      = Column(String(20),  unique=True, nullable=True, index=True)
    password   = Column(String(255), nullable=False)
    verified   = Column(Boolean, default=False)
    method     = Column(String(10), default="email")
    otp        = Column(String(6),  nullable=True)     # ✅ stores OTP temporarily
    created_at = Column(DateTime, default=datetime.utcnow)

    transactions  = relationship("Transaction",  back_populates="user", cascade="all, delete")
    settings      = relationship("UserSettings", back_populates="user", uselist=False, cascade="all, delete")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete")
    chat_sessions = relationship("ChatSession",  back_populates="user", cascade="all, delete")


class UserSettings(Base):
    __tablename__ = "user_settings"
    id                  = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id             = Column(UUID(as_uuid=False), nullable=False, unique=True, index=True)
    monthly_limit       = Column(Float,   nullable=True)
    daily_limit         = Column(Float,   nullable=True)
    block_transactions  = Column(Boolean, default=False)
    category_limits     = Column(JSON,    nullable=True)
    alert_preferences   = Column(JSON,    nullable=True)
    gmail_user          = Column(String(255), nullable=True)       # ✅ per-user Gmail
    gmail_app_password  = Column(String(255), nullable=True)       # ✅ per-user app password
    updated_at          = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="settings")


class Transaction(Base):
    __tablename__ = "transactions"
    id              = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id         = Column(UUID(as_uuid=False), nullable=False, index=True)
    date            = Column(String(10), nullable=False, index=True)
    time            = Column(String(8),  nullable=True)
    description     = Column(Text,       nullable=True)
    merchant        = Column(String(255),nullable=True)
    location        = Column(String(255),nullable=True)
    amount          = Column(Float,      nullable=False)
    currency        = Column(String(10), default="INR")
    type_of_payment = Column(String(50), nullable=True)
    category        = Column(String(100),nullable=True)
    sub_category    = Column(String(100),nullable=True)
    status          = Column(String(50), default="Completed")
    reference_id    = Column(String(100),nullable=True)
    notes           = Column(Text,       nullable=True)
    over_threshold  = Column(Boolean,    default=False)
    blocked         = Column(Boolean,    default=False)
    ai_categorized  = Column(Boolean,    default=False)
    created_at      = Column(DateTime,   default=datetime.utcnow)

    user = relationship("User", back_populates="transactions")


class Notification(Base):
    __tablename__ = "notifications"
    id         = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id    = Column(UUID(as_uuid=False), nullable=False, index=True)
    message    = Column(Text,    nullable=False)
    type       = Column(String(20), default="info")
    read       = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="notifications")


class ChatSession(Base):
    __tablename__ = "chat_sessions"
    id         = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id    = Column(UUID(as_uuid=False), nullable=False, index=True)
    thread_id  = Column(String(100), nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user     = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete")


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id         = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    session_id = Column(UUID(as_uuid=False), nullable=False, index=True)
    role       = Column(String(20), nullable=False)
    content    = Column(Text,       nullable=False)
    tool_calls = Column(JSON,       nullable=True)
    created_at = Column(DateTime,   default=datetime.utcnow)

    session = relationship("ChatSession", back_populates="messages")