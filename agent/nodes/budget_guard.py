# agent/nodes/budget_guard.py
"""
Budget Guard node — fetches budget health and explains it
in plain conversational language using Groq.
"""

import os
from langchain_groq import ChatGroq
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
from agent.state import AgentState
from agent.tools.budget_tools import get_budget_health
from agent.tools.transaction_tools import get_spending_summary

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

SYSTEM_PROMPT = """You are FinGuard AI, a friendly personal finance advisor for Indian students.
Explain the user's budget status clearly using the data provided.
Be conversational, specific with numbers, and give 1-2 actionable tips.
Use ₹ for currency. Keep it concise."""


async def budget_guard_node(state: AgentState) -> AgentState:
    """
    Fetches budget health + monthly summary from PostgreSQL,
    then asks Groq to explain it in plain language.
    """
    llm        = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.4, api_key=GROQ_API_KEY)
    user_id    = state["user_id"]
    user_input = state["user_input"]

    # Fetch data in parallel using separate tool calls
    health  = await get_budget_health.ainvoke({"user_id": user_id})
    summary = await get_spending_summary.ainvoke({"user_id": user_id, "period": "month"})

    context = f"""Here is the user's budget status:

Monthly budget limit : ₹{health.get('monthly_limit') or 'Not set'}
Daily spending limit : ₹{health.get('daily_limit')   or 'Not set'}
Spent this month     : ₹{health.get('month_spent', 0):.0f}
Spent today          : ₹{health.get('today_spent', 0):.0f}
Remaining balance    : ₹{health.get('remaining_balance') or 'N/A'}
Safe daily allowance : ₹{health.get('safe_daily_allowance') or 'N/A'}
Days left in month   : {health.get('days_left', 0)}
Monthly limit hit    : {'Yes ⚠️' if health.get('monthly_limit_exceeded') else 'No ✅'}
Daily limit hit      : {'Yes ⚠️' if health.get('daily_limit_exceeded')   else 'No ✅'}
Top spending category: {summary.get('top_category') or 'N/A'}
Total transactions   : {summary.get('transaction_count', 0)} this month

User asked: {user_input}"""

    response = await llm.ainvoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=context),
    ])

    return {
        **state,
        "budget_status":  health,
        "final_response": response.content,
        "messages":       [AIMessage(content=response.content)],
    }