from schemas import transaction
import joblib
import pandas as pd
from datetime import datetime

# In-memory "database"
transactions_db = []
cat_model = joblib.load(r"C:\myapp\ml_models\transaction_category_model.pkl")
sub_model = joblib.load(r"C:\myapp\ml_models\transaction_subcategory_model.pkl")

def create_transaction(txns, user_settings):
    created_txns = []
    for txn in txns:
        txn_df = pd.DataFrame([{
            "Merchant": txn.Merchant,
            "Amount": txn.Amount,
            "Payment_Type": txn.Type_of_Payment or "Card"
        }])

        txn.Category = cat_model.predict(txn_df)[0]
        txn.Sub_Category = sub_model.predict(txn_df)[0]
        txn.Date = txn.Date or datetime.now().strftime("%Y-%m-%d")
        txn.Time = txn.Time or datetime.now().strftime("%H:%M:%S")

        if txn.User_Id in user_settings:
            settings = user_settings[txn.User_Id]
            start_month = datetime.now().replace(day=1).strftime("%Y-%m-%d")
            user_monthly_txns = [
                t for t in transactions_db if t.User_Id == txn.User_Id and t.Date >= start_month
            ]
            monthly_spent = sum(abs(t.Amount) for t in user_monthly_txns if t.Amount < 0)

            if settings.Monthly_Limit and (monthly_spent + abs(txn.Amount)) > settings.Monthly_Limit:
                txn.Over_Threshold = True
                if settings.Block_Transactions:
                    txn.Blocked = True
                    txn.Notes = f"Transaction blocked! Exceeded monthly limit ₹{settings.Monthly_Limit}."
                    continue
                else:
                    txn.Notes = f"Warning: Monthly budget exceeded ₹{settings.Monthly_Limit}."

        transactions_db.append(txn)
        created_txns.append(txn)

    return {"message": "Transaction(s) added", "transactions": created_txns}

def get_transactions():
    return transactions_db

def update_transaction(transaction_id: int, updated_txn: transaction):
    for i, txn in enumerate(transactions_db):
        if i == transaction_id:
            transactions_db[i] = updated_txn
            return {"message": "Transaction updated", "transaction": updated_txn}
    return {"error": "Transaction not found"}

def delete_transaction(transaction_id: int):
    if 0 <= transaction_id < len(transactions_db):
        deleted = transactions_db.pop(transaction_id)
        return {"message": "Transaction deleted", "transaction": deleted}
    return {"error": "Transaction not found"}
