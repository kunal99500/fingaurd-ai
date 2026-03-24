# main.py
from dotenv import load_dotenv
load_dotenv()  # ✅ loads .env file automatically on startup

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import (
    auth_router,
    notification_router,
    transaction_router,
    summary_router,
    anomaly_router,
    budget_router,
    payment_router,
    insights_router,
    chat_router,
)

app = FastAPI(
    title="FinGuard AI — Smart Expense Tracker",
    description="AI-powered personal finance manager with daily limits, insights, and investment tips.",
    version="2.0.0"
)

# Allow Streamlit frontend to communicate with FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(notification_router.router, prefix="/notifications",  tags=["Notifications"])
app.include_router(transaction_router.router,  prefix="/transaction",    tags=["Transactions"])
app.include_router(summary_router.router,      prefix="/summary",        tags=["Summary"])
app.include_router(anomaly_router.router,      prefix="/anomaly",        tags=["Anomaly"])
app.include_router(budget_router.router,       prefix="/budget",         tags=["Budget"])
app.include_router(payment_router.router,                                tags=["Payments"])
app.include_router(insights_router.router,     prefix="/insights",       tags=["AI Insights"])
app.include_router(chat_router.router,         prefix="/chat",           tags=["AI Chat"])


@app.get("/")
def root():
    return {
        "message": "FinGuard AI backend running ✅",
        "docs": "/docs",
        "version": "2.0.0"
    }