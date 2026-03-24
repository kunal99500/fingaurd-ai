# agent/nodes/chat.py
"""
Chat node — general purpose conversational agent.
Has full financial context and uses conversation history
persisted in PostgreSQL via LangGraph checkpointer.
"""

import os
from langchain_groq import ChatGroq
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
from agent.state import AgentState
from agent.tools.budget_tools import get_budget_health
from agent.tools.transaction_tools import get_spending_summary, get_recent_transactions

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")


async def chat_node(state: AgentState) -> AgentState:
    """
    General conversation handler — answers any finance question
    with full context of the user's financial situation.
    Conversation history flows through LangGraph state.
    """
    llm     = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.6, api_key=GROQ_API_KEY)
    user_id = state["user_id"]

    # Fetch live financial context
    health  = await get_budget_health.ainvoke({"user_id": user_id})
    summary = await get_spending_summary.ainvoke({"user_id": user_id, "period": "month"})
    recent  = await get_recent_transactions.ainvoke({"user_id": user_id, "limit": 5})

    recent_text = "\n".join(
        f"  - {r['date']} | {r['merchant']} | ₹{abs(r['amount']):.0f} | {r['category']}"
        for r in recent
    ) if recent else "  No recent transactions"

    system = f"""You are FinGuard AI — a smart, friendly personal finance assistant for Indian students and young earners.
You have the user's real financial data below. Use it to give specific, relevant answers.

=== User Financial Snapshot ===
Monthly budget    : ₹{health.get('monthly_limit') or 'Not set'}
Daily limit       : ₹{health.get('daily_limit')   or 'Not set'}
Spent this month  : ₹{health.get('month_spent', 0):.0f}
Spent today       : ₹{health.get('today_spent', 0):.0f}
Remaining balance : ₹{health.get('remaining_balance') or 'N/A'}
Safe daily spend  : ₹{health.get('safe_daily_allowance') or 'N/A'}
Top category      : {summary.get('top_category') or 'N/A'}
Monthly limit hit : {'Yes ⚠️' if health.get('monthly_limit_exceeded') else 'No ✅'}

Recent transactions:
{recent_text}
=== End Snapshot ===

Guidelines:
- Be conversational, warm, and specific
- Use ₹ for all currency amounts
- Give actionable advice, not vague answers
- If user asks "can I afford X", calculate using their remaining balance
- Keep responses concise unless asked for detail"""

    # Build messages — system + full conversation history for multi-turn memory
    messages = [SystemMessage(content=system)]

    # Add last 10 messages from history for context
    for msg in state.get("messages", [])[-10:]:
        messages.append(msg)

    response = await llm.ainvoke(messages)

    return {
        **state,
        "final_response": response.content,
        "messages":       [AIMessage(content=response.content)],
    }