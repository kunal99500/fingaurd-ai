# routers/agent_router.py
import uuid
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from agent.graph import run_agent
from dependencies import get_current_user

router = APIRouter()


class AgentRequest(BaseModel):
    message:    str
    session_id: Optional[str] = None


class AgentResponse(BaseModel):
    response:           str
    intent:             str
    session_id:         str
    blocked:            bool = False
    transaction_result: Optional[dict] = None
    budget_status:      Optional[dict] = None


@router.post("/run", response_model=AgentResponse)
async def run_agent_endpoint(req: AgentRequest, user: dict = Depends(get_current_user)):
    user_id    = user["user_id"]
    session_id = req.session_id or f"session-{user_id}-{uuid.uuid4().hex[:8]}"
    try:
        result = await run_agent(user_id=user_id, session_id=session_id, user_input=req.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")
    return AgentResponse(
        response=result.get("response", ""),
        intent=result.get("intent", ""),
        session_id=session_id,
        blocked=result.get("blocked", False),
        transaction_result=result.get("transaction_result"),
        budget_status=result.get("budget_status"),
    )