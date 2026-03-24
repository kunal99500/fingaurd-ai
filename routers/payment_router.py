# routers/payment_router.py
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from dependencies import get_current_user
from repositories.payment_repository import process_synced_payment

router = APIRouter(prefix="/payment", tags=["Payments"])


@router.post("/sync")
async def sync_payment(
    message: str,
    user: dict = Depends(get_current_user),
    db:   AsyncSession = Depends(get_db)
):
    """
    Parse a UPI/bank SMS message and auto-create a transaction.
    """
    user_id = user["user_id"]
    result  = process_synced_payment(user_id, message)

    if result.get("blocked"):
        raise HTTPException(status_code=403, detail=result["message"])

    return {"message": result.get("message", "Transaction synced successfully.")}