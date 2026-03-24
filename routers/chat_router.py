# routers/chat_router.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from repositories.chat_repository import chat_with_ai

router = APIRouter()


class ChatMessage(BaseModel):
    role: str    # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    user_id: float
    message: str
    history: List[ChatMessage] = []


@router.post("/")
async def chat(req: ChatRequest):
    """
    Send a message to the AI financial advisor.
    Include conversation history for multi-turn chat.
    """
    try:
        history = [{"role": m.role, "content": m.content} for m in req.history]
        reply = await chat_with_ai(req.user_id, req.message, history)
        return {"reply": reply}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))