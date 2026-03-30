# agent/graph.py
"""
LangGraph graph — wires supervisor + 5 agents with PostgreSQL memory.
"""

import os
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from agent.state import AgentState
from agent.nodes.supervisor import supervisor_node, route_after_supervisor
from agent.nodes.categorizer import categorizer_node
from agent.nodes.budget_guard import budget_guard_node
from agent.nodes.insights import insights_node
from agent.nodes.investment import investment_node
from agent.nodes.chat import chat_node

DATABASE_URL = os.getenv("DATABASE_URL", "")
_graph = None


async def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("supervisor",       supervisor_node)
    graph.add_node("categorizer",      categorizer_node)
    graph.add_node("budget_guard",     budget_guard_node)
    graph.add_node("insights_agent",   insights_node)
    graph.add_node("investment_agent", investment_node)
    graph.add_node("chat_agent",       chat_node)
    graph.set_entry_point("supervisor")
    graph.add_conditional_edges(
        "supervisor",
        route_after_supervisor,
        {
            "categorizer":      "categorizer",
            "budget_guard":     "budget_guard",
            "insights_agent":   "insights_agent",
            "investment_agent": "investment_agent",
            "chat_agent":       "chat_agent",
        }
    )
    for node in ["categorizer", "budget_guard", "insights_agent", "investment_agent", "chat_agent"]:
        graph.add_edge(node, END)
    return graph.compile()


async def get_graph():
    global _graph
    if _graph is None:
        _graph = await build_graph()
    return _graph


async def run_agent(user_id: str, session_id: str, user_input: str) -> dict:
    graph  = await get_graph()
    config = {"configurable": {"thread_id": session_id}}

    initial_state = {
        "user_input":          user_input,
        "user_id":             user_id,
        "session_id":          session_id,
        "next_node":           "",
        "intent":              "",
        "messages":            [],
        "pending_transaction": None,
        "transaction_result":  None,
        "budget_status":       None,
        "blocked":             False,
        "block_reason":        None,
        "insights":            None,
        "investment_tips":     None,
        "market_news":         None,
        "final_response":      "",
    }

    final_state = None
    async for chunk in graph.astream(initial_state, config=config):
        final_state = chunk

    if not final_state:
        return {"response": "Something went wrong.", "intent": "unknown"}

    last = list(final_state.values())[-1]
    return {
        "response":           last.get("final_response", ""),
        "intent":             last.get("intent", ""),
        "blocked":            last.get("blocked", False),
        "transaction_result": last.get("transaction_result"),
        "budget_status":      last.get("budget_status"),
    }