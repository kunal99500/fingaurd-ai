# agent/nodes/insights.py
"""
Insights node — analyzes spending trends, detects anomalies,
and forecasts future spending using Groq + ML.
"""

import os
from langchain_groq import ChatGroq
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
from agent.state import AgentState
from agent.tools.transaction_tools import get_spending_summary
from agent.tools.insights_tools import forecast_spending, get_anomalies

GROQ_API_KEY = os.getenv('GROQ_API_KEY', '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')

SYSTEM_PROMPT = """You are FinGuard AI, a smart financial analyst.
Analyze the spending data provided and give clear, specific insights.
- Highlight unusual patterns or high-spend categories
- Comment on the spending trend (increasing/stable/decreasing)
- Give 2-3 concrete actionable recommendations
Use ₹ for currency. Be specific with numbers."""


async def insights_node(state: AgentState) -> AgentState:
    """
    Fetches monthly + weekly summaries, forecasts, and anomaly data,
    then uses Groq to generate a natural language insights report.
    """
    llm        = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.4, )
    user_id    = state["user_id"]
    user_input = state["user_input"]

    monthly   = await get_spending_summary.ainvoke({"user_id": user_id, "period": "month"})
    weekly    = await get_spending_summary.ainvoke({"user_id": user_id, "period": "week"})
    today     = await get_spending_summary.ainvoke({"user_id": user_id, "period": "today"})
    forecast  = await forecast_spending.ainvoke({"user_id": user_id})
    anomalies = await get_anomalies.ainvoke({"user_id": user_id})

    # Format category breakdowns
    def fmt_breakdown(bd: dict) -> str:
        return ", ".join(f"{k}: ₹{v:.0f}" for k, v in bd.items()) if bd else "No data"

    anomaly_text = ""
    if anomalies.get("anomalies"):
        anomaly_text = "\nSuspicious transactions:\n" + "\n".join(
            f"  - {a['merchant']} ₹{a['amount']:.0f} ({a['reason']})"
            for a in anomalies["anomalies"][:3]
        )

    context = f"""Spending analysis for user:

This month:
  Total spent      : ₹{monthly.get('total_spent', 0):.0f}
  Top category     : {monthly.get('top_category') or 'N/A'}
  Breakdown        : {fmt_breakdown(monthly.get('category_breakdown', {}))}
  Transactions     : {monthly.get('transaction_count', 0)}

This week:
  Total spent      : ₹{weekly.get('total_spent', 0):.0f}
  Breakdown        : {fmt_breakdown(weekly.get('category_breakdown', {}))}

Today:
  Total spent      : ₹{today.get('total_spent', 0):.0f}

Forecast:
  Trend            : {forecast.get('trend', 'N/A')}
  Avg daily spend  : ₹{forecast.get('average_daily_spend', 0):.0f}
  Next 7 days est. : ₹{forecast.get('next_week_total', 0):.0f}
  {forecast.get('message', '')}

Anomalies found    : {anomalies.get('anomalies_found', 0)}
{anomaly_text}

User asked: {user_input}"""

    response = await llm.ainvoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=context),
    ])

    return {
        **state,
        "insights": {
            "monthly":   monthly,
            "weekly":    weekly,
            "forecast":  forecast,
            "anomalies": anomalies,
        },
        "final_response": response.content,
        "messages":       [AIMessage(content=response.content)],
    }
