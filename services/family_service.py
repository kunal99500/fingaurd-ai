# services/family_service.py
"""
Family Finance Service
======================
Handles:
- Parent-Student linking
- Parent notifications on every transaction
- Emergency OTP system (parent approves limit override)
- Parent dashboard data
"""

import os
import random
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from utils.email_utils import send_email_otp
from utils.otp_utils import send_otp

MAILJET_CONFIGURED = bool(os.getenv("MAILJET_API_KEY"))


# ══════════════════════════════════════════
# PARENT-STUDENT LINKING
# ══════════════════════════════════════════

async def send_link_request(db: AsyncSession, student_id: str, parent_email: str) -> dict:
    """
    Student sends a link request to parent's email.
    Parent receives an email to accept/reject.
    """
    # Find parent by email
    res = await db.execute(
        text("SELECT id, email FROM users WHERE email = :email"),
        {"email": parent_email}
    )
    parent = res.fetchone()
    if not parent:
        return {"error": "No account found with this email. Ask your parent to sign up first."}

    parent_id = str(parent.id)

    # Check if already linked
    existing = await db.execute(text("""
        SELECT id, status FROM family_groups
        WHERE parent_id = :pid AND student_id = :sid
    """), {"pid": parent_id, "sid": student_id})
    if existing.fetchone():
        return {"error": "Already linked or request pending."}

    # Create pending link
    await db.execute(text("""
        INSERT INTO family_groups (parent_id, student_id, status, created_at)
        VALUES (:pid, :sid, 'pending', NOW())
    """), {"pid": parent_id, "sid": student_id})

    # Create default parent settings
    await db.execute(text("""
        INSERT INTO parent_settings (family_id, notify_every_transaction, notify_on_limit_exceeded, require_otp_on_exceed, parent_email)
        SELECT id, true, true, true, :email FROM family_groups
        WHERE parent_id = :pid AND student_id = :sid
    """), {"email": parent_email, "pid": parent_id, "sid": student_id})

    await db.commit()

    # Notify parent via email
    if MAILJET_CONFIGURED:
        from utils.email_utils import send_family_link_email
        send_family_link_email(parent_email, student_id)

    print(f"📧 Link request sent to {parent_email}")
    return {"message": f"Link request sent to {parent_email}. Ask your parent to accept it in the app."}


async def accept_link_request(db: AsyncSession, parent_id: str, student_id: str) -> dict:
    """Parent accepts the student's link request."""
    await db.execute(text("""
        UPDATE family_groups SET status = 'active'
        WHERE parent_id = :pid AND student_id = :sid
    """), {"pid": parent_id, "sid": student_id})
    await db.commit()
    return {"message": "✅ Family link activated! You will now receive notifications for all transactions."}


async def get_family_link(db: AsyncSession, user_id: str) -> dict:
    """Get family link status for a user (works for both parent and student)."""
    res = await db.execute(text("""
        SELECT fg.id, fg.parent_id, fg.student_id, fg.status,
               p.email as parent_email, s.email as student_email
        FROM family_groups fg
        JOIN users p ON p.id = fg.parent_id
        JOIN users s ON s.id = fg.student_id
        WHERE fg.parent_id = :uid OR fg.student_id = :uid
        ORDER BY fg.created_at DESC LIMIT 1
    """), {"uid": user_id})
    row = res.fetchone()
    if not row:
        return {"linked": False}
    return {
        "linked": True,
        "status": row.status,
        "parent_email": row.parent_email,
        "student_email": row.student_email,
        "is_parent": row.parent_id == user_id,
        "family_id": str(row.id),
    }


# ══════════════════════════════════════════
# PARENT NOTIFICATIONS
# ══════════════════════════════════════════

async def notify_parent_transaction(
    db: AsyncSession,
    student_id: str,
    merchant: str,
    amount: float,
    category: str,
    notes: str = ""
):
    """
    Send notification to parent whenever student makes a transaction.
    Called automatically from the categorizer agent.
    """
    # Get family link
    res = await db.execute(text("""
        SELECT fg.parent_id, fg.id as family_id, ps.notify_every_transaction,
               ps.notify_on_large_amount, ps.parent_email, ps.parent_phone
        FROM family_groups fg
        JOIN parent_settings ps ON ps.family_id = fg.id
        WHERE fg.student_id = :sid AND fg.status = 'active'
    """), {"sid": student_id})
    family = res.fetchone()

    if not family:
        return  # student not linked to parent

    if not family.notify_every_transaction:
        return  # notifications disabled

    # Check large amount threshold
    large_amount_alert = family.notify_on_large_amount and amount >= family.notify_on_large_amount

    message = (
        f"💳 Your child spent ₹{amount:.0f} at {merchant} ({category})"
        + (f"\n⚠️ Large transaction alert!" if large_amount_alert else "")
        + (f"\n📝 {notes}" if notes else "")
    )

    # Save notification in DB
    await db.execute(text("""
        INSERT INTO parent_notifications
        (parent_id, student_id, type, message, amount, merchant, category, created_at)
        VALUES (:pid, :sid, 'transaction', :msg, :amt, :merchant, :cat, NOW())
    """), {
        "pid": family.parent_id, "sid": student_id,
        "msg": message, "amt": amount,
        "merchant": merchant, "cat": category,
    })
    await db.commit()

    # Send email notification
    if family.parent_email and MAILJET_CONFIGURED:
        _send_parent_email_notification(family.parent_email, message)

    # Send SMS/WhatsApp (via console for now)
    print(f"📱 Parent notification: {message}")


async def notify_parent_limit_exceeded(
    db: AsyncSession,
    student_id: str,
    amount: float,
    limit_type: str,
    limit_value: float
):
    """Notify parent when student's limit is exceeded."""
    res = await db.execute(text("""
        SELECT fg.parent_id, ps.parent_email, ps.require_otp_on_exceed
        FROM family_groups fg
        JOIN parent_settings ps ON ps.family_id = fg.id
        WHERE fg.student_id = :sid AND fg.status = 'active'
    """), {"sid": student_id})
    family = res.fetchone()

    if not family:
        return

    message = f"🚨 Alert: Your child tried to spend ₹{amount:.0f} but exceeded their {limit_type} limit of ₹{limit_value:.0f}!"

    await db.execute(text("""
        INSERT INTO parent_notifications
        (parent_id, student_id, type, message, amount, created_at)
        VALUES (:pid, :sid, 'limit_exceeded', :msg, :amt, NOW())
    """), {"pid": family.parent_id, "sid": student_id, "msg": message, "amt": amount})
    await db.commit()

    if family.parent_email and MAILJET_CONFIGURED:
        _send_parent_email_notification(family.parent_email, message)

    print(f"🚨 Limit exceeded notification sent to parent")


# ══════════════════════════════════════════
# EMERGENCY OTP SYSTEM
# ══════════════════════════════════════════

async def request_emergency_otp(
    db: AsyncSession,
    student_id: str,
    amount: float,
    reason: str
) -> dict:
    """
    Student requests emergency OTP from parent to exceed limit.
    Parent gets notified and generates OTP.
    """
    res = await db.execute(text("""
        SELECT fg.id as family_id, fg.parent_id,
               ps.parent_email, ps.require_otp_on_exceed
        FROM family_groups fg
        JOIN parent_settings ps ON ps.family_id = fg.id
        WHERE fg.student_id = :sid AND fg.status = 'active'
    """), {"sid": student_id})
    family = res.fetchone()

    if not family:
        return {"error": "You are not linked to a parent account."}

    if not family.require_otp_on_exceed:
        return {"error": "OTP override not enabled by your parent."}

    # Generate OTP
    otp = str(random.randint(100000, 999999))
    expires_at = datetime.utcnow() + timedelta(minutes=10)

    # Save OTP
    await db.execute(text("""
        INSERT INTO emergency_otps (family_id, otp, amount, reason, used, expires_at, created_at)
        VALUES (:fid, :otp, :amt, :reason, false, :exp, NOW())
    """), {
        "fid": family.family_id, "otp": otp,
        "amt": amount, "reason": reason, "exp": expires_at
    })

    # Notify parent
    message = (
        f"🆘 Emergency payment request!\n\n"
        f"Your child wants to spend ₹{amount:.0f}\n"
        f"Reason: {reason}\n\n"
        f"OTP to approve: {otp}\n"
        f"Valid for 10 minutes.\n\n"
        f"Share this OTP ONLY if you approve this expense."
    )

    await db.execute(text("""
        INSERT INTO parent_notifications
        (parent_id, student_id, type, message, amount, created_at)
        VALUES (:pid, :sid, 'emergency_request', :msg, :amt, NOW())
    """), {"pid": family.parent_id, "sid": student_id, "msg": message, "amt": amount})

    await db.commit()

    if family.parent_email and MAILJET_CONFIGURED:
        _send_parent_email_notification(family.parent_email, message)

    print(f"🆘 Emergency OTP sent to parent: {otp}")

    return {
        "message": "Emergency request sent to your parent! Ask them for the OTP.",
        "otp_sent_to": family.parent_email or "parent's phone",
        "expires_in": "10 minutes",
    }


async def verify_emergency_otp(
    db: AsyncSession,
    student_id: str,
    otp: str,
    amount: float
) -> dict:
    """Verify the emergency OTP entered by student."""
    res = await db.execute(text("""
        SELECT eo.id, eo.otp, eo.expires_at, eo.used, eo.amount
        FROM emergency_otps eo
        JOIN family_groups fg ON fg.id = eo.family_id
        WHERE fg.student_id = :sid
          AND eo.used = false
          AND eo.expires_at > NOW()
        ORDER BY eo.created_at DESC LIMIT 1
    """), {"sid": student_id})
    record = res.fetchone()

    if not record:
        return {"valid": False, "error": "No valid OTP found. Request a new one."}

    if record.otp != otp:
        return {"valid": False, "error": "Incorrect OTP."}

    # Mark OTP as used
    await db.execute(text("""
        UPDATE emergency_otps SET used = true WHERE id = :id
    """), {"id": record.id})
    await db.commit()

    return {"valid": True, "message": "✅ Emergency OTP verified! Transaction approved by parent."}


# ══════════════════════════════════════════
# PARENT DASHBOARD
# ══════════════════════════════════════════

async def get_parent_dashboard(db: AsyncSession, parent_id: str) -> dict:
    """Full spending overview of all linked students for parent."""
    res = await db.execute(text("""
        SELECT fg.student_id, u.email as student_email,
               fg.status, fg.id as family_id
        FROM family_groups fg
        JOIN users u ON u.id = fg.student_id
        WHERE fg.parent_id = :pid AND fg.status = 'active'
    """), {"pid": parent_id})
    students = res.fetchall()

    if not students:
        return {"students": [], "message": "No students linked yet."}

    dashboard = []
    for s in students:
        # Get this month's spending
        month_start = datetime.now().replace(day=1).strftime("%Y-%m-%d")
        spend_res = await db.execute(text("""
            SELECT
                COALESCE(SUM(ABS(amount)), 0) as total_spent,
                COUNT(*) as txn_count
            FROM transactions
            WHERE user_id = :uid AND date >= :start AND amount < 0
        """), {"uid": s.student_id, "start": month_start})
        spend = spend_res.fetchone()

        # Get category breakdown
        cat_res = await db.execute(text("""
            SELECT category, SUM(ABS(amount)) as total
            FROM transactions
            WHERE user_id = :uid AND date >= :start AND amount < 0
            GROUP BY category ORDER BY total DESC LIMIT 5
        """), {"uid": s.student_id, "start": month_start})
        categories = {r.category or "Others": round(r.total, 2) for r in cat_res.fetchall()}

        # Get recent transactions
        txn_res = await db.execute(text("""
            SELECT merchant, amount, category, date
            FROM transactions
            WHERE user_id = :uid AND amount < 0
            ORDER BY date DESC, created_at DESC LIMIT 5
        """), {"uid": s.student_id})
        recent = [{"merchant": r.merchant, "amount": round(abs(r.amount), 2), "category": r.category, "date": r.date} for r in txn_res.fetchall()]

        # Get student settings
        settings_res = await db.execute(text("""
            SELECT monthly_limit, daily_limit FROM user_settings WHERE user_id = :uid
        """), {"uid": s.student_id})
        settings = settings_res.fetchone()

        dashboard.append({
            "student_id":    s.student_id,
            "student_email": s.student_email,
            "month_spent":   round(float(spend.total_spent), 2),
            "txn_count":     spend.txn_count,
            "monthly_limit": settings.monthly_limit if settings else None,
            "daily_limit":   settings.daily_limit   if settings else None,
            "categories":    categories,
            "recent_txns":   recent,
        })

    # Get unread parent notifications
    notif_res = await db.execute(text("""
        SELECT message, type, amount, merchant, created_at
        FROM parent_notifications
        WHERE parent_id = :pid AND read = false
        ORDER BY created_at DESC LIMIT 20
    """), {"pid": parent_id})
    notifications = [{"message": r.message, "type": r.type, "amount": r.amount, "merchant": r.merchant, "time": str(r.created_at)} for r in notif_res.fetchall()]

    return {
        "students":      dashboard,
        "notifications": notifications,
        "unread_count":  len(notifications),
    }


async def get_parent_notifications(db: AsyncSession, parent_id: str) -> list:
    """Get all notifications for a parent."""
    res = await db.execute(text("""
        SELECT pn.*, u.email as student_email
        FROM parent_notifications pn
        JOIN users u ON u.id = pn.student_id
        WHERE pn.parent_id = :pid
        ORDER BY pn.created_at DESC LIMIT 50
    """), {"pid": parent_id})
    rows = res.fetchall()

    # Mark all as read
    await db.execute(text("""
        UPDATE parent_notifications SET read = true WHERE parent_id = :pid
    """), {"pid": parent_id})
    await db.commit()

    return [{
        "message":       r.message,
        "type":          r.type,
        "amount":        r.amount,
        "merchant":      r.merchant,
        "category":      r.category,
        "student_email": r.student_email,
        "time":          str(r.created_at),
        "read":          r.read,
    } for r in rows]


# ══════════════════════════════════════════
# EMAIL HELPER
# ══════════════════════════════════════════

def _send_parent_email_notification(email: str, message: str):
    """Send email notification to parent."""
    try:
        import os
        from mailjet_rest import Client
        mailjet = Client(
            auth=(os.getenv("MAILJET_API_KEY"), os.getenv("MAILJET_SECRET_KEY")),
            version="v3.1"
        )
        data = {"Messages": [{
            "From": {"Email": os.getenv("SENDER_EMAIL"), "Name": "FinGuard AI"},
            "To": [{"Email": email}],
            "Subject": "FinGuard AI — Student Spending Alert",
            "TextPart": message,
            "HTMLPart": f"<div style='font-family:sans-serif;padding:20px'><h2>FinGuard AI Alert</h2><p>{message.replace(chr(10), '<br>')}</p></div>",
        }]}
        mailjet.send.create(data=data)
    except Exception as e:
        print(f"Email notification failed: {e}")