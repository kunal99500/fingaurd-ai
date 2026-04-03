# agent/nodes/categorizer.py
"""
Categorizer node — extracts transaction details from user message,
categorizes using Groq AI, checks budget limits, saves to PostgreSQL.
"""

import os
import re
import json
from langchain_groq import ChatGroq
from langchain_core.messages import AIMessage
from agent.state import AgentState
from agent.tools.budget_tools import check_limits
from agent.tools.transaction_tools import save_transaction

GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')


def _llm(temp=0.0):
    return ChatGroq(model="llama-3.3-70b-versatile", temperature=temp, )


async def categorizer_node(state: AgentState) -> AgentState:
    """
    1. Extract merchant/amount/payment_type from user message
    2. Categorize via Groq AI
    3. Check daily/monthly limits
    4. Save to PostgreSQL (or block)
    5. Return friendly response
    """
    llm       = _llm()
    user_input = state["user_input"]
    user_id    = state["user_id"]

    # ── Step 1: Extract transaction details ───────────────────
    extract_prompt = f"""Extract transaction details from this message.
Reply ONLY with valid JSON, no extra text:
{{
  "merchant": "string",
  "amount": 0.0,
  "payment_type": "UPI or Card or Cash or NetBanking",
  "description": "string"
}}

Message: {user_input}

Rules:
- amount must be a positive number
- If merchant not mentioned, use "Unknown"
- If payment_type not mentioned, use "UPI"
- description should be a short summary"""

    extract_res = await llm.ainvoke(extract_prompt)
    raw = extract_res.content.strip()
    match = re.search(r'\{.*\}', raw, re.DOTALL)
    try:
        txn_data = json.loads(match.group()) if match else {}
    except Exception:
        txn_data = {}

    merchant     = str(txn_data.get("merchant", "Unknown"))
    amount       = float(txn_data.get("amount", 0))
    payment_type = str(txn_data.get("payment_type", "UPI"))
    description  = str(txn_data.get("description", merchant))

    if amount <= 0:
        msg = "❌ Could not extract a valid amount. Please say something like:\n'I spent ₹250 on Zomato via UPI'"
        return {**state, "final_response": msg, "messages": [AIMessage(content=msg)]}

    # ── Step 2: Categorize via AI ─────────────────────────────
    cat_prompt = f"""Categorize this Indian transaction into EXACTLY ONE category:
Food, Shopping, Bills, Travel, Entertainment, Healthcare, Education, Others

Merchant: {merchant}
Amount: ₹{amount}
Payment: {payment_type}

Reply with ONLY the category name."""

    cat_res  = await llm.ainvoke(cat_prompt)
    category = cat_res.content.strip()
    valid_cats = ["Food", "Shopping", "Bills", "Travel", "Entertainment", "Healthcare", "Education", "Others"]
    if category not in valid_cats:
        category = "Others"

    # ── Step 3: Check budget limits ───────────────────────────
    limit_check = await check_limits.ainvoke({"user_id": user_id, "amount": amount})

    if limit_check.get("blocked"):
        msg = (
            f"🚫 **Transaction BLOCKED!**\n\n"
            f"{limit_check['reason']}\n\n"
            f"Daily remaining: ₹{limit_check.get('daily_remaining', 'N/A')}\n"
            f"Monthly remaining: ₹{limit_check.get('monthly_remaining', 'N/A')}"
        )
        return {
            **state,
            "blocked": True,
            "block_reason": limit_check["reason"],
            "final_response": msg,
            "messages": [AIMessage(content=msg)],
        }

    # ── Step 4: Save to PostgreSQL ────────────────────────────
    saved = await save_transaction.ainvoke({
        "user_id":      user_id,
        "merchant":     merchant,
        "amount":       amount,
        "payment_type": payment_type,
        "category":     category,
        "description":  description,
    })

    # ── Step 5: Build response ────────────────────────────────
    warning = f"\n\n⚠️ {limit_check['reason']}" if not limit_check.get("allowed") else ""

    response = (
        f"✅ **Transaction saved!**\n\n"
        f"🏪 **{merchant}** — ₹{amount:.0f}\n"
        f"📂 Category: **{category}** *(AI categorized)*\n"
        f"💳 Payment: {payment_type}\n"
        f"📅 Date: {saved.get('date', 'Today')}"
        f"{warning}"
    )

    if limit_check.get("daily_remaining") is not None:
        response += f"\n\n💡 Daily remaining: **₹{limit_check['daily_remaining']:.0f}**"
    if limit_check.get("monthly_remaining") is not None:
        response += f" | Monthly remaining: **₹{limit_check['monthly_remaining']:.0f}**"

    return {
        **state,
        "transaction_result": saved,
        "blocked": False,
        "final_response": response,
        "messages": [AIMessage(content=response)],
    }
