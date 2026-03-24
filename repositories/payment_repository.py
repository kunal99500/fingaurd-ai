import re
from datetime import datetime
from schemas import transaction
from repositories.transaction_repository import transactions_db
from repositories.budget_repository import user_settings

def process_synced_payment(user_id: float, message: str):
    """
    Parse payment message and create transaction only if user is within daily limit.
    Example message: "₹1,250 spent on Flipkart via UPI txn ID 123456 on 18 Oct 2025"
    """

    # Extract details from message
    amount_match = re.search(r"₹\s*([\d,]+(?:\.\d+)?)", message)
    merchant_match = re.search(r"on ([A-Za-z0-9 &\-\.]+)(?: via| txn|$)", message)
    date_match = re.search(r"on (\d{1,2} [A-Za-z]+ \d{4})", message)
    method_match = re.search(r"via (\w+)", message)

    if not amount_match:
        return {"error": "Could not extract amount"}

    amount = float(amount_match.group(1).replace(",", ""))
    merchant = merchant_match.group(1).strip() if merchant_match else "Unknown"
    date = datetime.now().strftime("%Y-%m-%d")
    if date_match:
        try:
            date = datetime.strptime(date_match.group(1), "%d %b %Y").strftime("%Y-%m-%d")
        except Exception:
            pass
    method = method_match.group(1) if method_match else "UPI"

    # ----------------------------
    # 🔒 Daily Limit Enforcement
    # ----------------------------
    if user_id in user_settings:
        settings = user_settings[user_id]
        daily_limit = (settings.Monthly_Limit or 0) / 30
        today_spent = sum(abs(t.Amount) for t in transactions_db if t.User_Id == user_id and t.Date == date and t.Amount < 0)

        if today_spent + amount > daily_limit:
            return {
                "blocked": True,
                "message": f"⚠️ Transaction of ₹{amount} blocked — daily spending limit ₹{daily_limit:.2f} exceeded!"
            }

    # ----------------------------
    # ✅ Record Transaction
    # ----------------------------
    txn = transaction(
        Id=datetime.now().timestamp(),
        User_Id=user_id,
        Date=date,
        Time=datetime.now().strftime("%H:%M:%S"),
        Description=f"Auto detected transaction from {merchant}",
        Merchant=merchant,
        Location="Auto-detected",
        Amount=-amount,
        Currency="INR",
        Type_of_Payment=method,
        Category=None,
        Sub_Category=None,
        Status_of_Transaction="Completed",
        Reference_Id=f"auto-{int(datetime.now().timestamp())}",
        Notes="Synced automatically from message",
    )

    transactions_db.append(txn)
    return {"message": f"Transaction auto-added: ₹{amount} at {merchant}"}
