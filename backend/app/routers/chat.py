import uuid
import json
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
from sqlalchemy import func as sql_func
from ..database import get_db
from ..models.chat_history import ChatHistory
from ..models.user import User
from ..schemas.chat import ChatMessage, ChatResponse, ChatSession
from ..utils.auth import get_current_user
from ..services.llm_client import get_llm_response, stream_llm_response

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/message", response_model=ChatResponse)
async def send_message(
    message: ChatMessage,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_msg = ChatHistory(
        user_id=current_user.id,
        session_id=message.session_id,
        role="user",
        content=message.content,
        agent_type=message.agent_type,
    )
    db.add(user_msg)
    db.commit()

    ai_content = await get_llm_response(db, message.agent_type, message.session_id, message.content, message.model_id)

    ai_msg = ChatHistory(
        user_id=current_user.id,
        session_id=message.session_id,
        role="assistant",
        content=ai_content,
        agent_type=message.agent_type,
    )
    db.add(ai_msg)
    db.commit()

    return ChatResponse(
        session_id=message.session_id,
        role="assistant",
        content=ai_content,
        agent_type=message.agent_type,
    )


@router.post("/message/stream")
async def send_message_stream(
    message: ChatMessage,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_msg = ChatHistory(
        user_id=current_user.id,
        session_id=message.session_id,
        role="user",
        content=message.content,
        agent_type=message.agent_type,
    )
    db.add(user_msg)
    db.commit()

    async def event_generator():
        full_content = ""
        try:
            async for chunk in stream_llm_response(db, message.agent_type, message.session_id, message.content, message.model_id):
                full_content += chunk
                data = json.dumps({"content": chunk}, ensure_ascii=False)
                yield f"data: {data}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"
            return

        ai_msg = ChatHistory(
            user_id=current_user.id,
            session_id=message.session_id,
            role="assistant",
            content=full_content,
            agent_type=message.agent_type,
        )
        db.add(ai_msg)
        db.commit()

        yield f"data: {json.dumps({'done': True}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/history/{session_id}", response_model=List[ChatResponse])
async def get_chat_history(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    messages = (
        db.query(ChatHistory)
        .filter(ChatHistory.session_id == session_id, ChatHistory.user_id == current_user.id)
        .order_by(ChatHistory.created_at)
        .all()
    )
    return [
        ChatResponse(
            session_id=m.session_id,
            role=m.role,
            content=m.content,
            agent_type=m.agent_type,
        )
        for m in messages
    ]


@router.get("/sessions", response_model=List[ChatSession])
async def get_chat_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    subq = (
        db.query(
            ChatHistory.session_id,
            ChatHistory.agent_type,
            sql_func.max(ChatHistory.created_at).label("max_time"),
        )
        .filter(ChatHistory.user_id == current_user.id, ChatHistory.role == "user")
        .group_by(ChatHistory.session_id, ChatHistory.agent_type)
        .subquery()
    )

    results = (
        db.query(
            ChatHistory.session_id,
            ChatHistory.content,
            ChatHistory.agent_type,
            ChatHistory.created_at,
        )
        .join(
            subq,
            (ChatHistory.session_id == subq.c.session_id)
            & (ChatHistory.agent_type == subq.c.agent_type)
            & (ChatHistory.created_at == subq.c.max_time),
        )
        .order_by(ChatHistory.created_at.desc())
        .all()
    )

    return [
        ChatSession(
            session_id=r.session_id,
            last_message=r.content[:50] if r.content else "",
            agent_type=r.agent_type,
            created_at=str(r.created_at),
        )
        for r in results
    ]


@router.post("/sessions/new")
async def create_new_session(
    current_user: User = Depends(get_current_user),
):
    session_id = str(uuid.uuid4())
    return {"session_id": session_id}


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db.query(ChatHistory).filter(
        ChatHistory.session_id == session_id, ChatHistory.user_id == current_user.id
    ).delete()
    db.commit()
    return {"message": "Session deleted"}
