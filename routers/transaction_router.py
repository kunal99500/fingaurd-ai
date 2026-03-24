from fastapi import APIRouter, HTTPException
from typing import List
from schemas import transaction
from repositories.transaction_repository import (
    create_transaction,
    get_transactions,
    update_transaction,
    delete_transaction,
    transactions_db,
)
from state import user_settings, transactions_db


router = APIRouter()

@router.post("/", summary="Add new transaction(s)")
def add_transactions(txns: List[transaction]):
    try:
        return create_transaction(txns, user_settings)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", summary="Get all transactions")
def fetch_transactions():
    try:
        return {"transactions": get_transactions()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{transaction_id}", summary="Update a transaction by index")
def update_transaction_route(transaction_id: int, updated_txn: transaction):
    try:
        result = update_transaction(transaction_id, updated_txn)
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{transaction_id}", summary="Delete a transaction by index")
def delete_transaction_route(transaction_id: int):
    try:
        result = delete_transaction(transaction_id)
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
