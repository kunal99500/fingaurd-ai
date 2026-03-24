# utils/otp_utils.py
import random
import time
import smtplib
from email.mime.text import MIMEText

# In-memory OTP storage
otp_store = {}  # {contact: {"otp": str, "timestamp": float}}

# ==============================
# ✉️ EMAIL CONFIG
# ==============================
EMAIL_SENDER = "your_email@gmail.com"      # replace with your email
EMAIL_PASSWORD = "your_app_password_here"  # Gmail App Password (not your login password)

def send_email_otp(recipient: str, otp: str):
    """Send OTP via email using Gmail SMTP."""
    try:
        msg = MIMEText(f"Your Smart Expense Tracker OTP is: {otp}\n\nValid for 5 minutes.")
        msg["Subject"] = "Smart Expense Tracker - OTP Verification"
        msg["From"] = EMAIL_SENDER
        msg["To"] = recipient

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
        print(f"📧 OTP sent to email: {recipient}")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")


# ==============================
# 🔢 GENERATE & SEND OTP
# ==============================
def send_otp(contact: str):
    """Generate and send OTP to either email or phone."""
    otp = str(random.randint(100000, 999999))
    otp_store[contact] = {"otp": otp, "timestamp": time.time()}

    if "@" in contact:
        send_email_otp(contact, otp)
    else:
        print(f"📱 OTP for {contact}: {otp}")  # Simulate SMS sending

    return {"message": f"OTP sent to {contact}"}


# ==============================
# ✅ VERIFY OTP
# ==============================
def verify_otp(contact: str, otp: str):
    """Verify the provided OTP."""
    if contact not in otp_store:
        return False
    data = otp_store[contact]
    if time.time() - data["timestamp"] > 300:  # 5 minutes
        del otp_store[contact]
        return False
    if data["otp"] == otp:
        del otp_store[contact]
        return True
    return False


# ==============================
# 🔁 RESEND OTP
# ==============================
def resend_otp(contact: str):
    """Resend the OTP if requested."""
    if contact not in otp_store:
        return send_otp(contact)
    otp_store[contact]["timestamp"] = time.time()
    otp = otp_store[contact]["otp"]

    if "@" in contact:
        send_email_otp(contact, otp)
    else:
        print(f"📱 Resent OTP for {contact}: {otp}")

    return {"message": f"OTP resent to {contact}"}
