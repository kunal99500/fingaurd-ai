# charts/insights_charts.py
import io
import base64
import matplotlib
matplotlib.use("Agg")  # ✅ Non-interactive backend — prevents crash on servers with no display
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime
from state import transactions_db  # ✅ use shared state, not a stale import


def _encode_figure() -> str:
    """Save current matplotlib figure to base64 PNG string."""
    buffer = io.BytesIO()
    plt.savefig(buffer, format="png", bbox_inches="tight")
    buffer.seek(0)
    encoded = base64.b64encode(buffer.read()).decode("utf-8")
    plt.close()
    return f"data:image/png;base64,{encoded}"


def plot_spending_trend(user_id: float):
    """Line chart of daily spending over time."""
    user_txns = [t for t in transactions_db if t.User_Id == user_id and t.Amount < 0]
    if not user_txns:
        return {"message": "No spending data found for this user"}

    df = pd.DataFrame([{
        "Date": datetime.strptime(t.Date, "%Y-%m-%d"),
        "Amount": abs(t.Amount)
    } for t in user_txns])
    df = df.groupby("Date", as_index=False).sum().sort_values("Date")

    plt.figure(figsize=(9, 4))
    plt.plot(df["Date"], df["Amount"], marker="o", linewidth=2, color="#0072ff", label="Daily Spend (₹)")
    plt.fill_between(df["Date"], df["Amount"], alpha=0.1, color="#0072ff")
    plt.title(f"Spending Trend — User {user_id}", fontsize=14)
    plt.xlabel("Date")
    plt.ylabel("Amount (₹)")
    plt.grid(True, alpha=0.3)
    plt.legend()

    return {"chart": _encode_figure()}


def plot_category_distribution(user_id: float):
    """Pie chart of spending by category."""
    user_txns = [t for t in transactions_db if t.User_Id == user_id and t.Amount < 0]
    if not user_txns:
        return {"message": "No spending data found for this user"}

    df = pd.DataFrame([{
        "Category": t.Category or "Uncategorized",
        "Amount": abs(t.Amount)
    } for t in user_txns])
    cat_sum = df.groupby("Category")["Amount"].sum()

    colors = ["#0072ff", "#00c6ff", "#5f2c82", "#49a09d", "#f7971e", "#e74c3c", "#2ecc71", "#9b59b6"]
    plt.figure(figsize=(6, 6))
    plt.pie(cat_sum, labels=cat_sum.index, autopct="%1.1f%%", startangle=140,
            colors=colors[:len(cat_sum)])
    plt.title(f"Category-wise Spending — User {user_id}", fontsize=13)

    return {"chart": _encode_figure()}


def plot_daily_vs_limit(user_id: float, daily_limit: float):
    """Bar chart comparing daily spending vs the daily limit."""
    user_txns = [t for t in transactions_db if t.User_Id == user_id and t.Amount < 0]
    if not user_txns:
        return {"message": "No spending data found for this user"}

    df = pd.DataFrame([{
        "Date": t.Date,
        "Amount": abs(t.Amount)
    } for t in user_txns])
    df = df.groupby("Date")["Amount"].sum().reset_index().tail(14)  # last 14 days

    plt.figure(figsize=(10, 4))
    bars = plt.bar(df["Date"], df["Amount"], color=[
        "#e74c3c" if v > daily_limit else "#2ecc71" for v in df["Amount"]
    ], alpha=0.85)
    plt.axhline(y=daily_limit, color="#0072ff", linestyle="--", linewidth=2, label=f"Daily Limit ₹{daily_limit}")
    plt.title("Daily Spending vs Your Limit (last 14 days)", fontsize=13)
    plt.xlabel("Date")
    plt.ylabel("Amount (₹)")
    plt.xticks(rotation=45)
    plt.legend()
    plt.tight_layout()

    return {"chart": _encode_figure()}