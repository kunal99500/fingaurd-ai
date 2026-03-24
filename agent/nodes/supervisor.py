# agent/nodes/supervisor.py
"""
Supervisor node — classifies user intent and routes to the right agent.
Uses Groq for fast intent classification.
"""

import os
from langchain_groq import ChatGroq
from agent.state import AgentState

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

INTENT_MAP = {
    "add_transaction":   "categorizer",
    "check_budget":      "budget_guard",
    "spending_insights": "insights_agent",
    "investment_advice": "investment_agent",
    "market_news":       "investment_agent",
    "chat":              "chat_agent",
}

SYSTEM_PROMPT = """You are a router for a personal finance AI app called FinGuard.
Classify the user's message into exactly one of these intents:

- add_transaction    → user wants to add/log a transaction or expense
- check_budget       → user asks about budget, limits, how much left to spend
- spending_insights  → user asks about spending trends, patterns, forecasts, summaries
- investment_advice  → user asks about investing, savings tips, where to put money
- market_news        → user asks about stock market, NSE, BSE, Nifty, share prices
- chat               → anything else: general questions, greetings, advice

Reply with ONLY the intent label, nothing else."""


async def supervisor_node(state: AgentState) -> AgentState:
    """Classify intent and set next_node in state."""
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0,
        api_key=GROQ_API_KEY,
        max_tokens=20,
    )

    user_input = state.get("user_input", "")
    response = await llm.ainvoke([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": user_input},
    ])

    intent = response.content.strip().lower()
    next_node = INTENT_MAP.get(intent, "chat_agent")

    return {
        **state,
        "intent": intent,
        "next_node": next_node,
    }


def route_after_supervisor(state: AgentState) -> str:
    """LangGraph conditional edge — returns name of next node."""
    return state.get("next_node", "chat_agent")