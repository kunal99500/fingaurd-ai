# routers/anomaly_router.py
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from repositories.anomaly_repository import get_anomalies, get_anomaly_report
from state import transactions_db  # ✅ always use shared state

router = APIRouter()


@router.get("/detect", summary="Detect spending anomalies")
def detect_anomalies(user_id: Optional[float] = Query(None)):
    try:
        txns = [t for t in transactions_db if t.User_Id == user_id] if user_id else transactions_db
        anomalies = get_anomalies(txns)
        return {"Anomalies": anomalies}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/report", summary="Get full anomaly report")
def anomaly_report(user_id: Optional[float] = Query(None)):
    try:
        txns = [t for t in transactions_db if t.User_Id == user_id] if user_id else transactions_db
        report = get_anomaly_report(txns)
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))