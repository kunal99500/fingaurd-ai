# repositories/chat_repository.py
"""
AI Chat Advisor — lets users ask questions like:
  "How am I doing this week?"
  "Where am I spending the most?"
  "Can I afford to spend ₹500 today?"
  "Give me a savings plan"
Uses Anthropic Claude API for responses.
"""

import os
import httpx
from datetime import datetime
from state import transactions_db, user_settings


ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = "claude-sonnet-4-20250514"


def build_financial_context(user_id: float) -> str:
    """Build a financial summary string to inject into the AI prompt."""
    today_str = datetime.now().strftime("%Y-%m-%d")
    start_month = datetime.now().replace(day=1).strftime("%Y-%m-%d")

    user_txns = [t for t in transactions_db if t.User_Id == user_id]
    monthly_txns = [t for t in user_txns if t.Date >= start_month and t.Amount < 0]
    today_txns = [t for t in user_txns if t.Date == today_str and t.Amount < 0]

    monthly_spent = sum(abs(t.Amount) for t in monthly_txns)
    today_spent = sum(abs(t.Amount) for t in today_txns)

    # Category breakdown
    from collections import defaultdict
    cat_breakdown = defaultdict(float)
    for t in monthly_txns:
        cat_breakdown[t.Category or "Uncategorized"] += abs(t.Amount)
    cat_str = ", ".join(f"{k}: ₹{v:.0f}" for k, v in sorted(cat_breakdown.items(), key=lambda x: -x[1]))

    # Settings
    settings = user_settings.get(user_id)
    monthly_limit = settings.Monthly_Limit if settings else None
    daily_limit = settings.Daily_Limit if settings else None
    block_mode = settings.Block_Transactions if settings else False

    days_left = 30 - datetime.now().day
    remaining = (monthly_limit - monthly_spent) if monthly_limit else None
    safe_daily = (remaining / days_left) if (remaining and days_left > 0) else None

    context = f"""
You are FinGuard AI, a smart personal finance advisor for a student/young earner in India.
Be friendly, concise, and use ₹ for currency. Give actionable advice.

=== USER FINANCIAL SNAPSHOT ===
Date: {today_str}
Monthly Budget: ₹{monthly_limit or 'Not set'}
Daily Limit: ₹{daily_limit or 'Not set'}
Block on Exceed: {'Yes' if block_mode else 'No'}

Monthly Spent So Far: ₹{monthly_spent:.2f}
Remaining Monthly Budget: ₹{remaining:.2f if remaining is not None else 'N/A'}
Days Left in Month: {days_left}
Safe Daily Allowance: ₹{safe_daily:.2f if safe_daily else 'N/A'}

Today's Spending: ₹{today_spent:.2f}
Total Transactions This Month: {len(monthly_txns)}

Category Breakdown (this month):
{cat_str or 'No transactions yet'}

Recent Transactions (last 5):
"""
    recent = sorted(user_txns, key=lambda t: t.Date, reverse=True)[:5]
    for t in recent:
        context += f"  - {t.Date} | {t.Merchant or 'Unknown'} | ₹{abs(t.Amount):.2f} | {t.Category or 'Uncategorized'}\n"

    context += "\n=== END SNAPSHOT ===\n"
    return context


async def chat_with_ai(user_id: float, user_message: str, history: list) -> str:
    """
    Send a message to Claude with financial context and conversation history.
    history = [{"role": "user"|"assistant", "content": str}, ...]
    """
    if not ANTHROPIC_API_KEY:
        return (
            "⚠️ AI Chat requires an Anthropic API key. "
            "Set the `ANTHROPIC_API_KEY` environment variable to enable this feature.\n\n"
            "Get your key at: https://console.anthropic.com"
        )

    system_prompt = build_financial_context(user_id)

    messages = history + [{"role": "user", "content": user_message}]

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": CLAUDE_MODEL,
                    "max_tokens": 1024,
                    "system": system_prompt,
                    "messages": messages,
                }
            )
            data = resp.json()
            if resp.status_code == 200:
                return data["content"][0]["text"]
            else:
                return f"❌ AI error: {data.get('error', {}).get('message', 'Unknown error')}"
        except Exception as e:
            return f"❌ Could not reach AI: {e}"


def chat_with_ai_sync(user_id: float, user_message: str, history: list) -> str:
    """Synchronous wrapper for Streamlit (which can't easily use async)."""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, chat_with_ai(user_id, user_message, history))
                return future.result()
        else:
            return loop.run_until_complete(chat_with_ai(user_id, user_message, history))
    except Exception as e:
        return f"❌ Chat error: {e}"