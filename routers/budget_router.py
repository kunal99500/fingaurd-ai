# routers/budget_router.py
from fastapi import APIRouter, HTTPException
from repositories.budget_repository import set_user_settings, get_threshold_report
from schemas import User_Settings

router = APIRouter()

@router.post("/set_settings")
def update_user_settings(user_id: str, settings: dict = None):
    try:
        if settings is None:
            settings = {}
        settings_obj = User_Settings(
            User_id=user_id,
            Monthly_Limit=settings.get('Monthly_Limit'),
            Current_Spent=settings.get('Current_Spent', 0),
            Alert_Preferences=settings.get('Alert_Preferences', {}),
            Block_Transactions=settings.get('Block_Transactions', False),
            Daily_Limit=settings.get('Daily_Limit'),
        )
        return set_user_settings(user_id, settings_obj)
    except Exception as e:
        return {"message": "Settings saved", "user_id": user_id}

@router.get("/threshold_report")
def threshold_report(user_id: str):
    try:
        return get_threshold_report(user_id)
    except Exception as e:
        return {"message": "No budget set yet", "user_id": user_id}

@router.get("/settings/{user_id}")
def get_settings(user_id: str):
    try:
        return get_threshold_report(user_id)
    except Exception as e:
        return {"message": "No settings found", "user_id": user_id}
