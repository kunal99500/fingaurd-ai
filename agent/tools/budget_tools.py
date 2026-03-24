# agent/tools/budget_tools.py
"""
Tools for checking and reporting budget limits from PostgreSQL.
Used by: budget_guard node, categorizer node
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
async def check_limits(user_id: str, amount: float) -> dict:
    """
    Check if a transaction amount will breach daily or monthly limits.
    Returns: allowed, blocked, reason, daily_remaining, monthly_remaining.
    """
    engine = _get_engine()
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    today_str   = datetime.now().strftime("%Y-%m-%d")
    month_start = datetime.now().replace(day=1).strftime("%Y-%m-%d")

    async with Session() as session:
        settings_res = await session.execute(
            text("SELECT * FROM user_settings WHERE user_id = :uid"),
            {"uid": user_id}
        )
        s = settings_res.fetchone()

        if not s:
            await engine.dispose()
            return {
                "allowed": True,
                "blocked": False,
                "reason": "No limits set yet. Set limits in Budget Settings.",
                "daily_remaining": None,
                "monthly_remaining": None,
            }

        today_res = await session.execute(text("""
            SELECT COALESCE(SUM(ABS(amount)), 0) AS spent
            FROM transactions
            WHERE user_id = :uid AND date = :today AND amount < 0
        """), {"uid": user_id, "today": today_str})
        today_spent = float(today_res.fetchone().spent)

        month_res = await session.execute(text("""
            SELECT COALESCE(SUM(ABS(amount)), 0) AS spent
            FROM transactions
            WHERE user_id = :uid AND date >= :start AND amount < 0
        """), {"uid": user_id, "start": month_start})
        month_spent = float(month_res.fetchone().spent)

        await engine.dispose()

    daily_limit   = s.daily_limit
    monthly_limit = s.monthly_limit
    block         = s.block_transactions

    daily_remaining   = round(daily_limit   - today_spent,  2) if daily_limit   else None
    monthly_remaining = round(monthly_limit - month_spent,  2) if monthly_limit else None

    # Daily limit breach
    if daily_limit and (today_spent + amount) > daily_limit:
        return {
            "allowed": not block,
            "blocked": bool(block),
            "reason": f"Daily limit ₹{daily_limit:.0f} exceeded! Already spent ₹{today_spent:.0f} today.",
            "daily_remaining": max(daily_remaining, 0),
            "monthly_remaining": monthly_remaining,
        }

    # Monthly limit breach
    if monthly_limit and (month_spent + amount) > monthly_limit:
        return {
            "allowed": not block,
            "blocked": bool(block),
            "reason": f"Monthly limit ₹{monthly_limit:.0f} exceeded! Already spent ₹{month_spent:.0f} this month.",
            "daily_remaining": daily_remaining,
            "monthly_remaining": max(monthly_remaining, 0),
        }

    return {
        "allowed": True,
        "blocked": False,
        "reason": "Within limits ✅",
        "daily_remaining": daily_remaining,
        "monthly_remaining": monthly_remaining,
    }


@tool
async def get_budget_health(user_id: str) -> dict:
    """
    Full budget health report for a user.
    Returns limits, spent amounts, remaining balance, safe daily allowance.
    """
    engine = _get_engine()
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    today       = datetime.now()
    today_str   = today.strftime("%Y-%m-%d")
    month_start = today.replace(day=1).strftime("%Y-%m-%d")
    days_left   = max(30 - today.day, 1)

    async with Session() as session:
        settings_res = await session.execute(
            text("SELECT * FROM user_settings WHERE user_id = :uid"), {"uid": user_id}
        )
        s = settings_res.fetchone()

        month_res = await session.execute(text("""
            SELECT COALESCE(SUM(ABS(amount)), 0) AS spent
            FROM transactions WHERE user_id = :uid AND date >= :start AND amount < 0
        """), {"uid": user_id, "start": month_start})
        month_spent = round(float(month_res.fetchone().spent), 2)

        today_res = await session.execute(text("""
            SELECT COALESCE(SUM(ABS(amount)), 0) AS spent
            FROM transactions WHERE user_id = :uid AND date = :today AND amount < 0
        """), {"uid": user_id, "today": today_str})
        today_spent = round(float(today_res.fetchone().spent), 2)

        await engine.dispose()

    monthly_limit = s.monthly_limit if s else None
    daily_limit   = s.daily_limit   if s else None
    remaining     = round(monthly_limit - month_spent, 2) if monthly_limit else None
    safe_daily    = round(remaining / days_left, 2) if remaining and days_left else None

    return {
        "monthly_limit":          monthly_limit,
        "daily_limit":            daily_limit,
        "month_spent":            month_spent,
        "today_spent":            today_spent,
        "remaining_balance":      remaining,
        "days_left":              days_left,
        "safe_daily_allowance":   safe_daily,
        "daily_limit_exceeded":   (today_spent > daily_limit)   if daily_limit   else False,
        "monthly_limit_exceeded": (month_spent > monthly_limit) if monthly_limit else False,
        "block_transactions":     bool(s.block_transactions)    if s             else False,
    }