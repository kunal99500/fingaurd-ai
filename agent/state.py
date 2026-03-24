# agent/state.py
from typing import Annotated, Optional
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    messages:            Annotated[list, add_messages]
    user_input:          str
    next_node:           str
    intent:              str
    user_id:             str
    session_id:          str
    pending_transaction: Optional[dict]
    transaction_result:  Optional[dict]
    budget_status:       Optional[dict]
    blocked:             bool
    block_reason:        Optional[str]
    insights:            Optional[dict]
    investment_tips:     Optional[list]
    market_news:         Optional[list]
    final_response:      str