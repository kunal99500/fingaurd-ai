# repositories/notification_repository.py
from datetime import datetime

# In-memory notifications database
notifications_db = {}  # {user_id: [{"type": str, "message": str, "timestamp": str}]}

def add_notification(user_id: float, message: str, type: str = "info"):
    """
    ✅ Add a new notification for a specific user.
    """
    if user_id not in notifications_db:
        notifications_db[user_id] = []

    notifications_db[user_id].append({
        "message": message,
        "type": type,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    return {"status": "added", "message": message}

def get_notifications(user_id: float):
    """
    ✅ Get all notifications for a user.
    """
    return notifications_db.get(user_id, [])

def clear_notifications(user_id: float):
    """
    ✅ Clear all notifications for a user.
    """
    notifications_db[user_id] = []
    return {"status": "cleared"}
