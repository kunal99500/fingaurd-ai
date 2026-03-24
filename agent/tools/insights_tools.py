# agent/tools/insights_tools.py
"""
Tools for spending trend analysis and forecasting.
Used by: insights node
"""

import os
from datetime import datetime, timedelta
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
async def forecast_spending(user_id: str) -> dict:
    """
    Forecast next 7 days spending using linear regression on past transactions.
    Returns trend direction, average daily spend, and per-day predictions.
    """
    import numpy as np
    from sklearn.linear_model import LinearRegression

    engine = _get_engine()
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with Session() as session:
        result = await session.execute(text("""
            SELECT date, SUM(ABS(amount)) AS daily_total
            FROM transactions
            WHERE user_id = :uid AND amount < 0
            GROUP BY date
            ORDER BY date
        """), {"uid": user_id})
        rows = result.fetchall()
        await engine.dispose()

    if len(rows) < 5:
        return {
            "message": "Need at least 5 days of transactions to forecast.",
            "forecast": [],
            "trend": "Not enough data",
            "average_daily_spend": 0,
            "next_week_total": 0,
        }

    dates   = [datetime.strptime(r.date, "%Y-%m-%d") for r in rows]
    amounts = [float(r.daily_total) for r in rows]
    base    = dates[0]
    day_nums = np.array([(d - base).days for d in dates]).reshape(-1, 1)

    model = LinearRegression()
    model.fit(day_nums, amounts)

    last_day = int(day_nums[-1][0])
    future   = np.arange(last_day + 1, last_day + 8).reshape(-1, 1)
    preds    = np.clip(model.predict(future), 0, None)

    avg    = round(float(np.mean(amounts)), 2)
    trend  = "Increasing 📈" if float(preds[-1]) > avg else "Stable / Decreasing 📉"

    forecast = [
        {
            "date":      (dates[-1] + timedelta(days=i + 1)).strftime("%Y-%m-%d"),
            "predicted": round(float(p), 2),
        }
        for i, p in enumerate(preds)
    ]

    return {
        "average_daily_spend": avg,
        "trend":               trend,
        "forecast":            forecast,
        "next_week_total":     round(float(sum(preds)), 2),
        "message":             f"Spending trend is {trend}. Estimated next week: ₹{sum(preds):.0f}",
    }


@tool
async def get_anomalies(user_id: str) -> dict:
    """
    Detect unusually large transactions using 2-standard-deviation rule.
    Returns list of suspicious transactions.
    """
    import statistics

    engine = _get_engine()
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with Session() as session:
        result = await session.execute(text("""
            SELECT merchant, amount, category, date
            FROM transactions
            WHERE user_id = :uid AND amount < 0
            ORDER BY date DESC
        """), {"uid": user_id})
        rows = result.fetchall()
        await engine.dispose()

    if len(rows) < 3:
        return {"anomalies": [], "message": "Not enough data for anomaly detection."}

    from collections import defaultdict
    cat_amounts = defaultdict(list)
    for r in rows:
        cat_amounts[r.category or "Uncategorized"].append(abs(r.amount))

    flagged = []
    for r in rows:
        cat = r.category or "Uncategorized"
        amounts = cat_amounts[cat]
        if len(amounts) < 2:
            continue
        mean = statistics.mean(amounts)
        std  = statistics.stdev(amounts)
        if std > 0 and abs(r.amount) > mean + 2 * std:
            flagged.append({
                "merchant":   r.merchant,
                "amount":     round(abs(r.amount), 2),
                "category":   cat,
                "date":       r.date,
                "reason":     f"₹{abs(r.amount):.0f} is unusually high for {cat} (avg ₹{mean:.0f})",
            })

    return {
        "total_transactions": len(rows),
        "anomalies_found":    len(flagged),
        "anomalies":          flagged[:10],
    }