import json
import time
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional

from ..database import get_db, SessionLocal
from ..entities import User
from ..dependencies import get_current_user
from ..services.chat_service import save_message
from ..agents.order_sales import stream_response as stream_order_agent_response
from ..utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/order-agent", tags=["order-agent"])


@router.post("/chat/stream")
async def order_agent_chat_stream(
    session_id: str,
    content: str,
    model_id: Optional[int] = None,
    knowledge_group_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    start_time = time.time()
    logger.info(
        f"[OrderAgent] New request: user_id={current_user.id}, session={session_id}, "
        f"content_length={len(content)}, model_id={model_id}, knowledge_group_id={knowledge_group_id}"
    )

    save_message(db, current_user.id, session_id, "user", content, "customer_service")

    async def event_generator():
        full_content = ""
        chunk_count = 0
        try:
            async for event_type, chunk in stream_order_agent_response(
                db, session_id, content,
                user_id=current_user.id,
                model_id=model_id,
                knowledge_group_id=knowledge_group_id,
            ):
                if event_type == "status":
                    payload = {"status": chunk["status"]} if isinstance(chunk, dict) else {"status": chunk}
                    if isinstance(chunk, dict) and chunk.get("search_query"):
                        payload["search_query"] = chunk["search_query"]
                    yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
                elif event_type == "search_results":
                    yield f"data: {json.dumps({'search_results': chunk}, ensure_ascii=False)}\n\n"
                elif event_type == "content" and chunk:
                    full_content += chunk
                    chunk_count += 1
                    data = json.dumps({"content": chunk}, ensure_ascii=False)
                    yield f"data: {data}\n\n"
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(
                f"[OrderAgent] Stream error: session={session_id}, elapsed={elapsed:.2f}s, error={type(e).__name__}: {e}"
            )
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"
            return

        save_db = SessionLocal()
        try:
            save_message(save_db, current_user.id, session_id, "assistant", full_content, "customer_service")
        finally:
            save_db.close()

        elapsed = time.time() - start_time
        logger.info(
            f"[OrderAgent] Completed: session={session_id}, elapsed={elapsed:.2f}s, chunks={chunk_count}, response_length={len(full_content)}"
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
