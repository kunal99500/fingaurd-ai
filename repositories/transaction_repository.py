import os
import joblib
import pandas as pd
from datetime import datetime
from schemas import transaction
from state import transactions_db, user_settings

# ✅ AI categorization replaces ML model — no .pkl needed
# Category is now handled by the LangGraph agent (categorizer node)
# This repository is kept for legacy REST API endpoints only

def create_transaction(txns, settings_map):
    created_txns = []
    today_str = datetime.now().strftime("%Y-%m-%d")

    for txn in txns:
        # Category comes from the request directly (set by agent or user)
        txn.Date = txn.Date or today_str
        txn.Time = txn.Time or datetime.now().strftime("%H:%M:%S")

        if txn.User_Id in settings_map:
            settings = settings_map[txn.User_Id]
            start_month = datetime.now().replace(day=1).strftime("%Y-%m-%d")
            monthly_spent = sum(
                abs(t.Amount) for t in transactions_db
                if t.User_Id == txn.User_Id and t.Date >= start_month and t.Amount < 0
            )
            if settings.Monthly_Limit and (monthly_spent + abs(txn.Amount)) > settings.Monthly_Limit:
                txn.Over_Threshold = True
                if settings.Block_Transactions:
                    txn.Blocked = True
                    txn.Notes = f"🚫 Blocked: monthly limit ₹{settings.Monthly_Limit} exceeded."
                    continue

            if settings.Daily_Limit:
                today_spent = sum(
                    abs(t.Amount) for t in transactions_db
                    if t.User_Id == txn.User_Id and t.Date == today_str and t.Amount < 0
                )
                if (today_spent + abs(txn.Amount)) > settings.Daily_Limit:
                    txn.Over_Threshold = True
                    if settings.Block_Transactions:
                        txn.Blocked = True
                        txn.Notes = f"🚫 Blocked: daily limit ₹{settings.Daily_Limit} exceeded."
                        continue

        transactions_db.append(txn)
        created_txns.append(txn)

    return {"message": "Transaction(s) processed", "transactions": created_txns}


def get_transactions(user_id: float = None):
    if user_id:
        return [t for t in transactions_db if t.User_Id == user_id]
    return transactions_db


def update_transaction(transaction_id: int, updated_txn: transaction):
    if 0 <= transaction_id < len(transactions_db):
        transactions_db[transaction_id] = updated_txn
        return {"message": "Transaction updated", "transaction": updated_txn}
    return {"error": "Transaction not found"}


def delete_transaction(transaction_id: int):
    if 0 <= transaction_id < len(transactions_db):
        deleted = transactions_db.pop(transaction_id)
        return {"message": "Transaction deleted", "transaction": deleted}
    return {"error": "Transaction not found"}