import requests
from mailjet_rest import Client
import os

MAILJET_API_KEY = "f91a655d8b37bdb2fdebb6a0df91adbc"
MAILJET_SECRET_KEY = "16365cb0e5b155c2c0e5fc7ea19a9884"
SENDER_EMAIL = "kunalmalik6396@gmail.com"  # verify this once in Mailjet

SENDER_NAME = "Smart Expense Tracker"

def send_email_otp(receiver_email: str, otp: str) -> bool:
    """Send OTP via Mailjet"""
    try:
        mailjet = Client(auth=(MAILJET_API_KEY, MAILJET_SECRET_KEY), version='v3.1')
        data = {
            'Messages': [
                {
                    "From": {
                        "Email": SENDER_EMAIL,
                        "Name": SENDER_NAME
                    },
                    "To": [
                        {
                            "Email": receiver_email,
                            "Name": "User"
                        }
                    ],
                    "Subject": "Your Smart Expense Tracker OTP Code",
                    "TextPart": f"Your OTP is {otp}",
                    "HTMLPart": f"""
                        <h2>🔐 Email Verification</h2>
                        <p>Your OTP for verification is:</p>
                        <h1 style='color:#0072ff'>{otp}</h1>
                        <p>This code will expire soon. Do not share it with anyone.</p>
                        <br>
                        <p>💸 Smart Expense Tracker</p>
                    """,
                }
            ]
        }
        result = mailjet.send.create(data=data)
        return result.status_code == 200
    except Exception as e:
        print(f"❌ Failed to send email OTP: {e}")
        return False