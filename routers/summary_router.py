# routers/summary_router.py
from fastapi import APIRouter, HTTPException, Query
from datetime import datetime, timedelta
from repositories.summary_repository import generate_summary, get_daily_summary
from state import transactions_db, user_settings  # ✅ import from state, not repositories

router = APIRouter()


@router.get("/daily", summary="Get last 7-day summary list")
def fetch_last_7_days_summary(user_id: float = Query(...)):
    try:
        summaries = get_daily_summary(user_id)
        if not summaries:
            raise HTTPException(status_code=404, detail="No transaction data found for this user.")
        return summaries
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching daily summaries: {e}")


@router.get("/today/{user_id}", summary="Get today's summary")
def fetch_today_summary(user_id: float):
    try:
        today = datetime.now()
        summary = generate_summary(user_id, transactions_db, user_settings, today, today)
        if not summary:
            raise HTTPException(status_code=404, detail="No transactions found for today.")
        return summary
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching today's summary: {e}")


@router.get("/weekly/{user_id}", summary="Get weekly summary")
def fetch_weekly_summary(user_id: float):
    try:
        today = datetime.now()
        summary = generate_summary(user_id, transactions_db, user_settings, today - timedelta(days=7), today)
        if not summary:
            raise HTTPException(status_code=404, detail="No transactions found for this week.")
        return summary
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching weekly summary: {e}")


@router.get("/monthly/{user_id}", summary="Get monthly summary")
def fetch_monthly_summary(user_id: float):
    try:
        today = datetime.now()
        summary = generate_summary(user_id, transactions_db, user_settings, today.replace(day=1), today)
        if not summary:
            raise HTTPException(status_code=404, detail="No transactions found for this month.")
        return summary
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching monthly summary: {e}")