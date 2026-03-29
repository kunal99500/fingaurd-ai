# main.py
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from database import init_db
# Import all models so SQLAlchemy registers them before init_db
from models import User, UserSettings, Transaction, Notification, ChatSession, ChatMessage
from models_family import FamilyGroup, ParentSettings, EmergencyOTP, ParentNotification
from models_family import FamilyGroup, ParentSettings, EmergencyOTP, ParentNotification
from routers import (
    auth_router, notification_router, transaction_router,
    summary_router, anomaly_router, budget_router,
    payment_router, insights_router, agent_router,
)
from routers import family_router
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ──
    try:
        from models import User, UserSettings, Transaction, Notification, ChatSession, ChatMessage
        from models_family import FamilyGroup, ParentSettings, EmergencyOTP, ParentNotification
        await init_db()
        print("✅ Database tables ready")
    except Exception as e:
        print(f"❌ Database init error: {e}")
    yield
    print("👋 Shutting down")


app = FastAPI(
    title="FinGuard AI",
    description="Agentic personal finance manager powered by LangGraph + Groq + Supabase",
    version="3.0.0",
    lifespan=lifespan,
)



app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8081",
        "http://localhost:3000",
        "http://127.0.0.1:8081",
        "https://fingaurd-ai.onrender.com",
        "*"
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(transaction_router.router,  prefix="/transaction",    tags=["Transactions"])
app.include_router(budget_router.router,       prefix="/budget",         tags=["Budget"])
app.include_router(insights_router.router,     prefix="/insights",       tags=["Insights"])
app.include_router(summary_router.router,      prefix="/summary",        tags=["Summary"])
app.include_router(anomaly_router.router,      prefix="/anomaly",        tags=["Anomaly"])
app.include_router(payment_router.router,                                tags=["Payments"])
app.include_router(notification_router.router, prefix="/notifications",  tags=["Notifications"])
app.include_router(agent_router.router,        prefix="/agent",          tags=["AI Agent"])
app.include_router(family_router.router,       prefix="/family",         tags=["Family"])

@app.get("/")
def root():
    return {"message": "FinGuard AI v3.0 running ✅", "docs": "/docs"}