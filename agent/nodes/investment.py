# agent/nodes/investment.py
"""
Investment node — fetches live market news and generates
personalized investment tips based on user savings.
"""

import os
from langchain_groq import ChatGroq
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
from agent.state import AgentState
from agent.tools.budget_tools import get_budget_health
from agent.tools.news_tools import fetch_market_news, get_investment_tips

GROQ_API_KEY = os.getenv('GROQ_API_KEY', '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')

SYSTEM_PROMPT = """You are FinGuard AI, a friendly investment advisor for Indian students and young earners.
Based on the user's savings and current market news, give specific, beginner-friendly advice.
- Mention specific Indian options: SIP, Nifty 50, PPF, FD, NPS, Sovereign Gold Bond
- Keep it practical and actionable
- Reference relevant market news if it helps
Use ₹ for currency."""


async def investment_node(state: AgentState) -> AgentState:
    """
    Fetches user's savings amount, investment tips, and live market news,
    then uses Groq to generate a personalized investment recommendation.
    """
    llm        = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.5, )
    user_id    = state["user_id"]
    user_input = state["user_input"]

    health   = await get_budget_health.ainvoke({"user_id": user_id})
    savings  = max(float(health.get("remaining_balance") or 0), 0)
    tips     = await get_investment_tips.ainvoke({"monthly_savings": savings})
    news     = await fetch_market_news.ainvoke({"query": "Indian stock market NSE BSE Nifty mutual fund SIP"})

    tips_text = "\n".join(f"- {t}" for t in tips[:5])
    news_text = "\n".join(
        f"- {n['title']} ({n['source']})" for n in news[:4]
    )

    context = f"""User financial context:
Monthly savings this month : ₹{savings:.0f}
Monthly budget limit       : ₹{health.get('monthly_limit') or 'Not set'}
Month spent so far         : ₹{health.get('month_spent', 0):.0f}

Personalized tips based on savings:
{tips_text}

Latest market news:
{news_text}

User asked: {user_input}"""

    response = await llm.ainvoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=context),
    ])

    return {
        **state,
        "investment_tips": tips,
        "market_news":     news,
        "final_response":  response.content,
        "messages":        [AIMessage(content=response.content)],
    }
