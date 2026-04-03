# repositories/budget_repository.py
from datetime import datetime
from schemas import User_Settings, Threshold_Report
from state import user_settings, transactions_db


def set_user_settings(user_id: str, settings: User_Settings):
    user_settings[str(user_id)] = settings
    return {"message": f"Settings updated for user {user_id}", "settings": settings}


def get_threshold_report(user_id: str):
    user_id = str(user_id)
    if user_id not in user_settings:
        return {
            "User_id": user_id,
            "Monthly_Limit": 0,
            "Current_Spent": 0,
            "Remaining_Balance": 0,
            "Limit_Exceeded": False,
            "Suggested_Action": "Set your monthly budget in Settings to get insights.",
            "Daily_Limit": 0,
            "Today_Spent": 0,
        }

    settings = user_settings[user_id]
    start_month = datetime.now().replace(day=1).strftime("%Y-%m-%d")
    today_str = datetime.now().strftime("%Y-%m-%d")

    monthly_spent = sum(
        abs(t.Amount) for t in transactions_db
        if str(t.User_Id) == user_id and t.Date >= start_month and t.Amount < 0
    )
    today_spent = sum(
        abs(t.Amount) for t in transactions_db
        if str(t.User_Id) == user_id and t.Date == today_str and t.Amount < 0
    )

    monthly_limit = settings.Monthly_Limit or 0
    daily_limit = settings.Daily_Limit or 0
    remaining = monthly_limit - monthly_spent
    exceeded = monthly_spent > monthly_limit if monthly_limit > 0 else False

    today = datetime.now()
    days_left = max((datetime.now().replace(month=today.month % 12 + 1, day=1) - today).days, 1)
    daily_allowance = max(remaining / days_left, 0) if remaining > 0 else 0

    return {
        "User_id": user_id,
        "Monthly_Limit": monthly_limit,
        "Current_Spent": round(monthly_spent, 2),
        "Remaining_Balance": round(remaining, 2),
        "Limit_Exceeded": exceeded,
        "Daily_Limit": daily_limit,
        "Today_Spent": round(today_spent, 2),
        "Daily_Remaining": round(max(daily_limit - today_spent, 0), 2),
        "Suggested_Daily_Allowance": round(daily_allowance, 2),
        "Days_Left_In_Month": days_left,
        "Suggested_Action": (
            f"Budget exceeded by Rs.{abs(remaining):.0f}. Cut down expenses."
            if exceeded else f"You can spend Rs.{daily_allowance:.0f} per day safely."
        )
    }
