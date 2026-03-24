import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression
from repositories.transaction_repository import transactions_db
from repositories.budget_repository import user_settings


def prepare_user_data(user_id: float):
    """
    Convert user transactions into a DataFrame for ML modeling.
    """
    user_txns = [
        t for t in transactions_db if t.User_Id == user_id and t.Amount < 0
    ]

    if not user_txns:
        return None

    df = pd.DataFrame([{
        "Date": datetime.strptime(t.Date, "%Y-%m-%d"),
        "Amount": abs(t.Amount)
    } for t in user_txns])

    df = df.groupby("Date", as_index=False).sum()
    df = df.sort_values("Date")
    return df


def predict_daily_spending(user_id: float):
    """
    Calculate how much user can spend daily for the rest of the month.
    """
    if user_id not in user_settings:
        return {"error": "No settings found for this user."}

    settings = user_settings[user_id]
    total_limit = settings.Monthly_Limit or 0

    start_month = datetime.now().replace(day=1).strftime("%Y-%m-%d")
    user_txns = [t for t in transactions_db if t.User_Id == user_id and t.Date >= start_month]
    spent = sum(abs(t.Amount) for t in user_txns if t.Amount < 0)

    remaining = total_limit - spent
    days_left = 30 - datetime.now().day
    daily_allowance = remaining / days_left if days_left > 0 else 0

    return {
        "User_ID": user_id,
        "Remaining_Balance": round(remaining, 2),
        "Days_Left": days_left,
        "Daily_Allowance": round(daily_allowance, 2)
    }


def analyze_spending_trends(user_id: float):
    """
    Analyze past spending and forecast next week's expenses using simple ML.
    """
    df = prepare_user_data(user_id)
    if df is None or df.shape[0] < 5:
        return {"message": "Not enough transaction data for trend analysis"}

    # Convert dates to day numbers
    df["DayNum"] = (df["Date"] - df["Date"].min()).dt.days

    X = df[["DayNum"]]
    y = df["Amount"]
    model = LinearRegression()
    model.fit(X, y)

    # Predict next 7 days
    last_day = df["DayNum"].max()
    future_days = np.arange(last_day + 1, last_day + 8).reshape(-1, 1)
    predictions = model.predict(future_days)

    forecast_dates = [df["Date"].max() + timedelta(days=i) for i in range(1, 8)]
    forecast_data = [
        {"date": d.strftime("%Y-%m-%d"), "predicted_spent": round(p, 2)}
        for d, p in zip(forecast_dates, predictions)
    ]

    avg_spent = round(df["Amount"].mean(), 2)
    trend_msg = "Increasing" if predictions[-1] > avg_spent else "Stable/Decreasing"

    return {
        "user_id": user_id,
        "average_daily_spent": avg_spent,
        "predicted_next_week": forecast_data,
        "trend": trend_msg,
        "message": f"Your spending trend seems {trend_msg}. Estimated next week’s total: ₹{sum(predictions):.2f}"
    }


def generate_ai_insights(user_id: float):
    """
    Combine all insights into one summary response.
    """
    daily_prediction = predict_daily_spending(user_id)
    trend_analysis = analyze_spending_trends(user_id)

    recommendations = []
    if "error" in daily_prediction:
        recommendations.append("⚠️ Please set your monthly budget first.")
    elif daily_prediction["Daily_Allowance"] < 200:
        recommendations.append("🚨 Low daily allowance left. Reduce expenses immediately.")
    elif daily_prediction["Daily_Allowance"] > 1000:
        recommendations.append("✅ You have enough balance — spend wisely!")

    if trend_analysis.get("trend") == "Increasing":
        recommendations.append("⚠️ Spending pattern is increasing — watch your expenses.")
    elif trend_analysis.get("trend") == "Stable/Decreasing":
        recommendations.append("✅ Great job! Your spending trend is stable or decreasing.")

    return {
        "user_id": user_id,
        "daily_prediction": daily_prediction,
        "trend_analysis": trend_analysis,
        "recommendations": recommendations
    }
