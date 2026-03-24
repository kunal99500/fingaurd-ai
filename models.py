from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy.orm import declarative_base

import datetime

Base = declarative_base()


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    account_number = Column(String, nullable=True)
    date = Column(DateTime, default=datetime.datetime.utcnow)
    description = Column(String)
    merchant = Column(String, nullable=True)
    location = Column(String, nullable=True)
    amount = Column(Float)
    currency = Column(String)
    type_of_payment = Column(String)
    category = Column(String, nullable=True)
    sub_category = Column(String, nullable=True)
    status = Column(String, nullable=True)
    reference_id = Column(String, nullable=True)
    notes = Column(String, nullable=True)
    over_threshold = Column(Boolean, default=False)
    blocked = Column(Boolean, default=False)
