import io
import base64
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from datetime import datetime
from state import transactions_db


def _encode_figure() -> str:
    buffer = io.BytesIO()
    plt.savefig(buffer, format="png", bbox_inches="tight")
    buffer.seek(0)
    encoded = base64.b64encode(buffer.read()).decode("utf-8")
    plt.close()
    return f"data:image/png;base64,{encoded}"


def plot_spending_trend(user_id: float):
    user_txns = [t for t in transactions_db if t.User_Id == user_id and t.Amount < 0]
    if not user_txns:
        return {"message": "No spending data found for this user"}

    daily = {}
    for t in user_txns:
        daily[t.Date] = daily.get(t.Date, 0) + abs(t.Amount)

    dates = sorted(daily.keys())
    amounts = [daily[d] for d in dates]
    date_objs = [datetime.strptime(d, "%Y-%m-%d") for d in dates]

    plt.figure(figsize=(9, 4))
    plt.plot(date_objs, amounts, marker="o", linewidth=2, color="#0072ff", label="Daily Spend")
    plt.fill_between(date_objs, amounts, alpha=0.1, color="#0072ff")
    plt.title(f"Spending Trend", fontsize=14)
    plt.xlabel("Date")
    plt.ylabel("Amount (Rs.)")
    plt.grid(True, alpha=0.3)
    plt.legend()
    return {"chart": _encode_figure()}


def plot_category_distribution(user_id: float):
    user_txns = [t for t in transactions_db if t.User_Id == user_id and t.Amount < 0]
    if not user_txns:
        return {"message": "No spending data found for this user"}

    cat_totals = {}
    for t in user_txns:
        cat = t.Category or "Uncategorized"
        cat_totals[cat] = cat_totals.get(cat, 0) + abs(t.Amount)

    colors = ["#0072ff", "#00c6ff", "#5f2c82", "#49a09d", "#f7971e", "#e74c3c", "#2ecc71", "#9b59b6"]
    plt.figure(figsize=(6, 6))
    plt.pie(list(cat_totals.values()), labels=list(cat_totals.keys()), autopct="%1.1f%%", startangle=140, colors=colors[:len(cat_totals)])
    plt.title("Category-wise Spending", fontsize=13)
    return {"chart": _encode_figure()}
