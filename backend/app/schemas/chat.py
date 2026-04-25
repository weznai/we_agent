from pydantic import BaseModel
from typing import Optional, List


class ChatMessage(BaseModel):
    session_id: str
    content: str
    agent_type: Optional[str] = "chat"
    model_id: Optional[int] = None


class ChatResponse(BaseModel):
    session_id: str
    role: str
    content: str
    agent_type: str


class ChatSession(BaseModel):
    session_id: str
    last_message: str
    agent_type: str
    created_at: str


class TranslateRequest(BaseModel):
    content: str
    source_lang: Optional[str] = "auto"
    target_lang: str = "en"
