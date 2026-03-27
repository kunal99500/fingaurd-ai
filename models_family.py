# models_family.py
"""
Family finance models — Parent-Student relationship,
emergency OTP system, and parent notifications.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Boolean, DateTime, Text, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database import Base


def gen_uuid():
    return str(uuid.uuid4())


class FamilyGroup(Base):
    """Links a parent to one or more students."""
    __tablename__ = "family_groups"

    id          = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    parent_id   = Column(UUID(as_uuid=False), nullable=False, index=True)  # parent user id
    student_id  = Column(UUID(as_uuid=False), nullable=False, index=True)  # student user id
    status      = Column(String(20), default="pending")   # pending | active | rejected
    created_at  = Column(DateTime, default=datetime.utcnow)

    parent_settings = relationship("ParentSettings", back_populates="family", cascade="all, delete")
    emergency_otps  = relationship("EmergencyOTP",   back_populates="family", cascade="all, delete")


class ParentSettings(Base):
    """Parent-defined rules for their student."""
    __tablename__ = "parent_settings"

    id                        = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    family_id                 = Column(UUID(as_uuid=False), nullable=False, index=True)
    notify_every_transaction  = Column(Boolean, default=True)   # notify on every txn
    notify_on_limit_exceeded  = Column(Boolean, default=True)   # notify when limit hit
    notify_on_large_amount    = Column(Float,   nullable=True)  # notify if txn > X
    blocked_categories        = Column(Text,    nullable=True)  # comma-separated categories
    monthly_allowance         = Column(Float,   nullable=True)  # allowance set by parent
    require_otp_on_exceed     = Column(Boolean, default=True)   # OTP needed to override limit
    parent_email              = Column(String(255), nullable=True)
    parent_phone              = Column(String(20),  nullable=True)
    updated_at                = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    family = relationship("FamilyGroup", back_populates="parent_settings")


class EmergencyOTP(Base):
    """OTP issued by parent to allow student to exceed limit in emergency."""
    __tablename__ = "emergency_otps"

    id          = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    family_id   = Column(UUID(as_uuid=False), nullable=False, index=True)
    otp         = Column(String(6),  nullable=False)
    amount      = Column(Float,      nullable=True)   # amount student wants to spend
    reason      = Column(Text,       nullable=True)   # reason student gave
    used        = Column(Boolean,    default=False)
    expires_at  = Column(DateTime,   nullable=False)
    created_at  = Column(DateTime,   default=datetime.utcnow)

    family = relationship("FamilyGroup", back_populates="emergency_otps")


class ParentNotification(Base):
    """Notifications sent to parents about student spending."""
    __tablename__ = "parent_notifications"

    id          = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    parent_id   = Column(UUID(as_uuid=False), nullable=False, index=True)
    student_id  = Column(UUID(as_uuid=False), nullable=False, index=True)
    type        = Column(String(50),  nullable=False)   # transaction | limit_exceeded | emergency_request
    message     = Column(Text,        nullable=False)
    amount      = Column(Float,       nullable=True)
    merchant    = Column(String(255), nullable=True)
    category    = Column(String(100), nullable=True)
    read        = Column(Boolean,     default=False)
    created_at  = Column(DateTime,    default=datetime.utcnow)