# routers/notification_router.py
from fastapi import APIRouter, HTTPException
from repositories.notification_repository import (
    add_notification,
    get_notifications,
    clear_notifications
)

router = APIRouter()

@router.get("/{user_id}")
def fetch_notifications(user_id: float):
    """
    ✅ Fetch all notifications for a user.
    """
    try:
        notifications = get_notifications(user_id)
        return {"notifications": notifications}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching notifications: {str(e)}")

@router.post("/{user_id}")
def add_user_notification(user_id: float, message: str, type: str = "info"):
    """
    ✅ Add a new notification for a user.
    """
    try:
        return add_notification(user_id, message, type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding notification: {str(e)}")

@router.delete("/{user_id}")
def delete_user_notifications(user_id: float):
    """
    ✅ Clear all notifications for a user.
    """
    try:
        return clear_notifications(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing notifications: {str(e)}")
