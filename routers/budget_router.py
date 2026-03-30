# routers/budget_router.py
from fastapi import APIRouter, HTTPException
from repositories.budget_repository import set_user_settings, get_threshold_report

router = APIRouter()


@router.post("/set_settings")
def update_user_settings(user_id: str, settings: dict):
    try:
        from schemas import User_Settings
        settings_obj = User_Settings(**settings)
        return set_user_settings(user_id, settings_obj)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/threshold_report")
def threshold_report(user_id: str):
    try:
        return get_threshold_report(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating report: {str(e)}")
