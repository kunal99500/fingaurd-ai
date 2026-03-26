import os
import httpx
from datetime import datetime, timedelta
from langchain_groq import ChatGroq
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text
from state import transactions_db, user_settings

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")
DATABASE_URL = os.getenv("DATABASE_URL", "")


def _simple_linear_regression(x, y):
    n = len(x)
    if n < 2:
        return 0, 0
    x_mean = sum(x) / n
    y_mean = sum(y) / n
    numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
    denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
    slope = numerator / denominator if denominator != 0 else 0
    intercept = y_mean - slope * x_mean
    return slope, intercept


def predict_daily_spending(user_id: float):
    if user_id not in user_settings:
        return {"error": "No settings found. Please set your monthly budget first."}

    settings = user_settings[user_id]
    monthly_limit = settings.Monthly_Limit or 0
    daily_limit = settings.Daily_Limit
    today_str = datetime.now().strftime("%Y-%m-%d")
    start_month = datetime.now().replace(day=1).strftime("%Y-%m-%d")

    user_txns = [t for t in transactions_db if t.User_Id == user_id and t.Date >= start_month]
    monthly_spent = sum(abs(t.Amount) for t in user_txns if t.Amount < 0)
    today_spent = sum(abs(t.Amount) for t in transactions_db if t.User_Id == user_id and t.Date == today_str and t.Amount < 0)

    remaining = monthly_limit - monthly_spent
    days_left = max(30 - datetime.now().day, 1)
    suggested_daily = remaining / days_left if days_left > 0 else 0

    result = {
        "User_ID": user_id,
        "Monthly_Limit": monthly_limit,
        "Monthly_Spent": round(monthly_spent, 2),
        "Remaining_Balance": round(remaining, 2),
        "Days_Left_In_Month": days_left,
        "Suggested_Daily_Allowance": round(suggested_daily, 2),
        "Today_Spent": round(today_spent, 2),
    }

    if daily_limit:
        result["Daily_Limit"] = daily_limit
        result["Daily_Remaining"] = round(max(daily_limit - today_spent, 0), 2)
        result["Daily_Limit_Exceeded"] = today_spent > daily_limit

    return result


def analyze_spending_trends(user_id: float):
    user_txns = [t for t in transactions_db if t.User_Id == user_id and t.Amount < 0]
    if len(user_txns) < 5:
        return {"message": "Not enough transaction data for trend analysis (need at least 5 days)."}

    daily = {}
    for t in user_txns:
        daily[t.Date] = daily.get(t.Date, 0) + abs(t.Amount)

    sorted_dates = sorted(daily.keys())
    base = datetime.strptime(sorted_dates[0], "%Y-%m-%d")
    x = [(datetime.strptime(d, "%Y-%m-%d") - base).days for d in sorted_dates]
    y = [daily[d] for d in sorted_dates]

    slope, intercept = _simple_linear_regression(x, y)
    avg = sum(y) / len(y)

    last_day = x[-1]
    future = [last_day + i for i in range(1, 8)]
    preds = [max(slope * xi + intercept, 0) for xi in future]

    last_date = datetime.strptime(sorted_dates[-1], "%Y-%m-%d")
    forecast = [
        {"date": (last_date + timedelta(days=i+1)).strftime("%Y-%m-%d"), "predicted_spent": round(p, 2)}
        for i, p in enumerate(preds)
    ]

    trend = "Increasing" if preds[-1] > avg else "Stable/Decreasing"

    return {
        "user_id": user_id,
        "average_daily_spent": round(avg, 2),
        "predicted_next_week": forecast,
        "trend": trend,
        "estimated_next_week_total": round(sum(preds), 2),
        "message": f"Spending trend is {trend}. Estimated next week: Rs.{sum(preds):.2f}"
    }


def generate_investment_tips(user_id: float):
    tips = []
    if user_id not in user_settings:
        return {"tips": ["Set your monthly budget first to get personalized investment tips."]}

    settings = user_settings[user_id]
    monthly_limit = settings.Monthly_Limit or 0
    start_month = datetime.now().replace(day=1).strftime("%Y-%m-%d")
    monthly_spent = sum(abs(t.Amount) for t in transactions_db if t.User_Id == user_id and t.Date >= start_month and t.Amount < 0)
    monthly_savings = monthly_limit - monthly_spent

    if monthly_savings <= 0:
        tips.append("You are over budget. Focus on cutting expenses before investing.")
    elif monthly_savings < 500:
        tips.append(f"You saved Rs.{monthly_savings:.0f}. Start with Rs.100/month SIP on Groww.")
    elif monthly_savings < 2000:
        tips.append(f"You saved Rs.{monthly_savings:.0f}. Consider a Nifty 50 Index Fund SIP.")
        tips.append("Keep 3 months expenses in a high-interest savings account.")
    else:
        tips.append(f"Great savings of Rs.{monthly_savings:.0f}! Diversify: 60% equity, 30% debt, 10% gold.")
        tips.append("Consider PPF account for tax-free returns up to 7.1% p.a.")

    tips += [
        "Rule of 72: at 12% returns your money doubles in 6 years.",
        "Always maintain 6-month emergency fund before investing in equities.",
        "Beginner? Start: Nifty 50 Index Fund SIP (Rs.500/month minimum on Groww).",
    ]
    return {"user_id": user_id, "monthly_savings": round(monthly_savings, 2), "tips": tips}


def generate_ai_insights(user_id: float):
    daily_prediction = predict_daily_spending(user_id)
    trend_analysis = analyze_spending_trends(user_id)
    investment_tips = generate_investment_tips(user_id)
    recommendations = []

    if "error" not in daily_prediction:
        remaining = daily_prediction.get("Remaining_Balance", 0)
        if remaining < 0:
            recommendations.append("You have exceeded your monthly budget!")
        elif daily_prediction.get("Daily_Limit_Exceeded"):
            recommendations.append("Today daily limit exceeded. Be careful with spending.")
        else:
            recommendations.append(f"You can safely spend Rs.{daily_prediction.get('Suggested_Daily_Allowance', 0):.0f}/day.")

    trend = trend_analysis.get("trend", "")
    if "Increasing" in trend:
        recommendations.append("Spending is trending up. Review your last 7 days.")
    else:
        recommendations.append("Spending trend is stable or decreasing. Keep it up!")

    return {
        "user_id": user_id,
        "daily_prediction": daily_prediction,
        "trend_analysis": trend_analysis,
        "investment_tips": investment_tips.get("tips", []),
        "recommendations": recommendations
    }
