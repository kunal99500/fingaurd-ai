# repositories/summary_repository.py
from schemas import Daily_Summary
from datetime import datetime, timedelta
from collections import defaultdict


def generate_summary(user_id: float, transactions_db, user_settings, start_date, end_date):
    """
    Generate spending summary for a specific user and date range.
    """
    user_txns = [
        t for t in transactions_db
        if t.User_Id == user_id and start_date.strftime("%Y-%m-%d") <= t.Date <= end_date.strftime("%Y-%m-%d")
    ]

    if not user_txns:
        return None

    total_spent = sum(abs(t.Amount) for t in user_txns if t.Amount < 0)
    category_breakdown = defaultdict(float)
    for t in user_txns:
        category_breakdown[t.Category] += abs(t.Amount)

    top_category = max(category_breakdown, key=category_breakdown.get)
    top_merchant = max(user_txns, key=lambda x: abs(x.Amount)).Merchant
    notes = f"Spent ₹{total_spent} between {start_date.date()} and {end_date.date()}, mostly on {top_category}."

    if user_id in user_settings:
        settings = user_settings[user_id]
        if settings.Monthly_Limit and total_spent > settings.Monthly_Limit:
            notes += f" ⚠️ Budget exceeded ₹{settings.Monthly_Limit}."

    return Daily_Summary(
        User_Id=user_id,
        Date=f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
        Total_Spent=total_spent,
        Transaction_Today=user_txns,
        Category_Breakdown=category_breakdown,
        Top_Merchant=top_merchant,
        Notes=notes
    )


def get_daily_summary(user_id: float, transactions_db=None):
    """
    Return a list of daily summaries for the past 7 days.
    """
    if transactions_db is None:
        from repositories.transaction_repository import transactions_db  # lazy import

    today = datetime.now()
    summaries = []
    for i in range(7):
        date = today - timedelta(days=i)
        summary = generate_summary(user_id, transactions_db, {}, date, date)
        if summary:
            summaries.append(summary)
    return list(reversed(summaries))
