# repositories/budget_repository.py
from datetime import datetime
from schemas import User_Settings, Threshold_Report
from state import user_settings, transactions_db


def set_user_settings(user_id: float, settings: User_Settings):
    """
    Stores or updates a user's spending settings and limits.
    """
    user_settings[user_id] = settings
    return {"message": f"Settings updated for user {user_id}", "settings": settings}


def get_threshold_report(user_id: float):
    """
    Calculates user's monthly spending, remaining balance, and alerts.
    """
    if user_id not in user_settings:
        return {"message": "No settings found for this user"}

    settings = user_settings[user_id]
    start_month = datetime.now().replace(day=1).strftime("%Y-%m-%d")

    user_monthly_txns = [
        t for t in transactions_db
        if t.User_Id == user_id and t.Date >= start_month
    ]
    monthly_spent = sum(abs(t.Amount) for t in user_monthly_txns if t.Amount < 0)

    remaining = (settings.Monthly_Limit or 0) - monthly_spent
    exceeded = monthly_spent > (settings.Monthly_Limit or float("inf"))

    # Predict daily allowed spending for remaining days
    today = datetime.now()
    remaining_days = (today.replace(day=28) + datetime.timedelta(days=4)).replace(day=1) - today
    remaining_days = remaining_days.days or 1  # avoid divide by zero

    daily_allowance = max(remaining / remaining_days, 0)

    return Threshold_Report(
        User_id=user_id,
        Monthly_Limit=settings.Monthly_Limit or 0,
        Current_Spent=monthly_spent,
        Remaining_Balance=remaining,
        Limit_Exceeded=exceeded,
        Suggested_Action=(
            f"Budget exceeded by ₹{abs(remaining)}. Cut down expenses."
            if exceeded else f"You can spend ₹{daily_allowance:.2f} per day safely."
        )
    )
