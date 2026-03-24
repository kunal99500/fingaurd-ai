# routers/payment_router.py
from fastapi import APIRouter, HTTPException, Header
from repositories.payment_repository import process_synced_payment
from repositories.auth_repository import decode_access_token, users_db

router = APIRouter(prefix="/payment", tags=["Payments"])


@router.post("/sync")
def sync_payment(message: str, authorization: str = Header(None)):
    """
    Parse a UPI/bank SMS message and auto-create a transaction.
    Enforces the user's daily limit — blocks if exceeded and Block_Transactions is on.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    token = authorization.replace("Bearer ", "").strip()
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    sub = payload.get("sub")  # email or phone
    user = next(
        (u for u in users_db if u.get("email") == sub or u.get("phone") == sub),
        None
    )
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    result = process_synced_payment(user["user_id"], message)

    if result.get("blocked"):
        raise HTTPException(status_code=403, detail=result["message"])

    return {"message": result.get("message", "Transaction synced successfully.")}