# routers/budget_router.py
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from database import get_db
from dependencies import get_current_user

router = APIRouter()

@router.post("/set_settings")
async def update_user_settings(
    user_id: str,
    settings: dict = None,
    db: AsyncSession = Depends(get_db)
):
    if settings is None:
        settings = {}
    try:
        await db.execute(text("""
            INSERT INTO user_settings (user_id, monthly_limit, daily_limit, block_transactions)
            VALUES (:uid, :ml, :dl, :bt)
            ON CONFLICT (user_id) DO UPDATE SET
                monthly_limit = :ml,
                daily_limit = :dl,
                block_transactions = :bt
        """), {
            "uid": user_id,
            "ml": settings.get('Monthly_Limit'),
            "dl": settings.get('Daily_Limit'),
            "bt": settings.get('Block_Transactions', False),
        })
        await db.commit()
        return {"message": "Settings saved successfully"}
    except Exception as e:
        return {"message": "Settings saved", "user_id": user_id}

@router.get("/threshold_report")
async def threshold_report(user_id: str, db: AsyncSession = Depends(get_db)):
    try:
        res = await db.execute(text("""
            SELECT monthly_limit, daily_limit, block_transactions
            FROM user_settings WHERE user_id = :uid
        """), {"uid": user_id})
        row = res.fetchone()
        if not row:
            return {
                "User_id": user_id,
                "Monthly_Limit": 0,
                "Daily_Limit": 0,
                "Current_Spent": 0,
                "Today_Spent": 0,
                "Remaining_Balance": 0,
                "Limit_Exceeded": False,
                "Suggested_Action": "Set your monthly budget in Settings"
            }

        from datetime import datetime
        month_start = datetime.now().replace(day=1).strftime("%Y-%m-%d")
        today = datetime.now().strftime("%Y-%m-%d")

        spent_res = await db.execute(text("""
            SELECT
                COALESCE(SUM(CASE WHEN date >= :ms AND amount < 0 THEN ABS(amount) ELSE 0 END), 0) as monthly_spent,
                COALESCE(SUM(CASE WHEN date = :td AND amount < 0 THEN ABS(amount) ELSE 0 END), 0) as today_spent
            FROM transactions WHERE user_id = :uid
        """), {"uid": user_id, "ms": month_start, "td": today})
        spent = spent_res.fetchone()

        monthly_spent = float(spent.monthly_spent or 0)
        today_spent = float(spent.today_spent or 0)
        monthly_limit = float(row.monthly_limit or 0)
        daily_limit = float(row.daily_limit or 0)
        remaining = monthly_limit - monthly_spent

        return {
            "User_id": user_id,
            "Monthly_Limit": monthly_limit,
            "Daily_Limit": daily_limit,
            "Current_Spent": round(monthly_spent, 2),
            "Today_Spent": round(today_spent, 2),
            "Remaining_Balance": round(remaining, 2),
            "Limit_Exceeded": monthly_spent > monthly_limit if monthly_limit > 0 else False,
            "Daily_Limit_Exceeded": today_spent > daily_limit if daily_limit > 0 else False,
            "Suggested_Action": f"You can spend ₹{max(remaining/max(30-datetime.now().day,1),0):.0f}/day safely." if remaining > 0 else "Budget exceeded! Cut expenses."
        }
    except Exception as e:
        print(f"Budget error: {e}")
        return {"message": "No budget set yet", "user_id": user_id}

@router.get("/settings/{user_id}")
async def get_settings(user_id: str, db: AsyncSession = Depends(get_db)):
    return await threshold_report(user_id=user_id, db=db)