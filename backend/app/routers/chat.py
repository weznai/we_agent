import json
import time
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..entities import User
from ..dependencies import get_current_user
from ..schemas.chat import ChatMessage, ChatResponse, ChatSession
from ..services.chat_service import save_message, get_history, get_sessions, create_session, delete_session
from ..services.llm_client import get_llm_response, stream_llm_response
from ..utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/message", response_model=ChatResponse)
async def send_message(
    message: ChatMessage,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    start_time = time.time()
    logger.info(
        f"[Chat] New message: user_id={current_user.id}, session={message.session_id}, agent_type={message.agent_type}, content_length={len(message.content)}"
    )

    save_message(
        db, current_user.id, message.session_id, "user", message.content, message.agent_type
    )

    ai_content = await get_llm_response(
        db, message.agent_type, message.session_id, message.content, message.model_id,
        images=message.images,
    )

    save_message(
        db, current_user.id, message.session_id, "assistant", ai_content, message.agent_type
    )

    elapsed = time.time() - start_time
    logger.info(
        f"[Chat] Message completed: session={message.session_id}, elapsed={elapsed:.2f}s, response_length={len(ai_content)}"
    )

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
    start_time = time.time()
    logger.info(
        f"[Chat Stream] New streaming message: user_id={current_user.id}, session={message.session_id}, agent_type={message.agent_type}, content_length={len(message.content)}"
    )

    save_message(
        db, current_user.id, message.session_id, "user", message.content, message.agent_type
    )

    async def event_generator():
        full_content = ""
        chunk_count = 0
        reasoning_content = None
        try:
            async for chunk in stream_llm_response(
                db, message.agent_type, message.session_id, message.content, message.model_id,
                images=message.images,
            ):
                if isinstance(chunk, dict) and "__meta__" in chunk:
                    reasoning_content = chunk["__meta__"].get("reasoning_content")
                    continue
                full_content += chunk
                chunk_count += 1
                data = json.dumps({"content": chunk}, ensure_ascii=False)
                yield f"data: {data}\n\n"
        except Exception as e:
            logger.error(
                f"[Chat Stream] Stream error: session={message.session_id}, error={type(e).__name__}: {e}"
            )
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"
            return

        save_message(
            db, current_user.id, message.session_id, "assistant", full_content, message.agent_type,
            reasoning_content=reasoning_content,
        )

        elapsed = time.time() - start_time
        logger.info(
            f"[Chat Stream] Completed: session={message.session_id}, elapsed={elapsed:.2f}s, chunks={chunk_count}, response_length={len(full_content)}"
        )

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
    return get_history(db, current_user.id, session_id)


@router.get("/sessions", response_model=List[ChatSession])
async def get_chat_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_sessions(db, current_user.id)


@router.post("/sessions/new")
async def create_new_session(
    current_user: User = Depends(get_current_user),
):
    session_id = create_session()
    return {"session_id": session_id}


@router.delete("/sessions/{session_id}")
async def delete_chat_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return delete_session(db, current_user.id, session_id)
