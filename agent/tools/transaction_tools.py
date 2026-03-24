# agent/tools/transaction_tools.py
"""
Tools for saving and fetching transactions from PostgreSQL.
Used by: categorizer node
"""

import os
from datetime import datetime
from langchain_core.tools import tool
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text

DATABASE_URL = os.getenv("DATABASE_URL", "")


def _get_engine():
    url = DATABASE_URL
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    return create_async_engine(url, echo=False)


@tool
async def save_transaction(
    user_id: str,
    merchant: str,
    amount: float,
    payment_type: str,
    category: str,
    description: str = "",
    date: str = "",
) -> dict:
    """
    Save a categorized transaction to PostgreSQL.
    Amount should be positive — stored as negative (expense).
    Returns saved transaction dict.
    """
    from models import Transaction

    engine = _get_engine()
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with Session() as session:
        txn = Transaction(
            user_id=user_id,
            date=date or datetime.now().strftime("%Y-%m-%d"),
            time=datetime.now().strftime("%H:%M:%S"),
            description=description or merchant,
            merchant=merchant,
            amount=-abs(amount),
            currency="INR",
            type_of_payment=payment_type,
            category=category,
            status="Completed",
            ai_categorized=True,
        )
        session.add(txn)
        await session.commit()
        await session.refresh(txn)
        await engine.dispose()
        return {
            "id": str(txn.id),
            "merchant": txn.merchant,
            "amount": txn.amount,
            "category": txn.category,
            "date": txn.date,
            "payment_type": txn.type_of_payment,
            "ai_categorized": True,
        }


@tool
async def get_spending_summary(user_id: str, period: str = "month") -> dict:
    """
    Get spending summary for a user from PostgreSQL.
    period options: 'today' | 'week' | 'month'
    Returns total spent, category breakdown, top category.
    """
    engine = _get_engine()
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    today = datetime.now()
    if period == "today":
        from_date = today.strftime("%Y-%m-%d")
    elif period == "week":
        from datetime import timedelta
        from_date = (today - timedelta(days=7)).strftime("%Y-%m-%d")
    else:
        from_date = today.replace(day=1).strftime("%Y-%m-%d")

    async with Session() as session:
        result = await session.execute(text("""
            SELECT category,
                   COUNT(*)            AS txn_count,
                   SUM(ABS(amount))    AS total
            FROM transactions
            WHERE user_id  = :uid
              AND date     >= :from_date
              AND amount   < 0
            GROUP BY category
            ORDER BY total DESC
        """), {"uid": user_id, "from_date": from_date})

        rows = result.fetchall()
        await engine.dispose()

    breakdown = {r.category or "Uncategorized": round(r.total, 2) for r in rows}
    total = sum(breakdown.values())

    return {
        "period": period,
        "from_date": from_date,
        "total_spent": round(total, 2),
        "category_breakdown": breakdown,
        "top_category": max(breakdown, key=breakdown.get) if breakdown else None,
        "transaction_count": sum(r.txn_count for r in rows),
    }


@tool
async def get_recent_transactions(user_id: str, limit: int = 10) -> list:
    """
    Fetch the most recent transactions for a user.
    Returns list of transaction dicts.
    """
    engine = _get_engine()
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with Session() as session:
        result = await session.execute(text("""
            SELECT merchant, amount, category, date, type_of_payment, notes
            FROM transactions
            WHERE user_id = :uid
            ORDER BY date DESC, created_at DESC
            LIMIT :lim
        """), {"uid": user_id, "lim": limit})

        rows = result.fetchall()
        await engine.dispose()

    return [
        {
            "merchant": r.merchant,
            "amount": round(r.amount, 2),
            "category": r.category,
            "date": r.date,
            "payment_type": r.type_of_payment,
            "notes": r.notes,
        }
        for r in rows
    ]