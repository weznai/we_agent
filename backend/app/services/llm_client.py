import time
from typing import AsyncGenerator, Optional

from openai import AsyncOpenAI
from sqlalchemy.orm import Session
from fastapi import HTTPException

from ..entities import ChatHistory
from ..services.model_service import resolve_model
from ..utils.logger import get_logger

logger = get_logger(__name__)

SYSTEM_PROMPTS = {
    "chat": "You are a helpful, knowledgeable AI assistant. Respond in the same language the user uses. Be concise and accurate.",
    "translation": "You are a professional translator. Translate the given text accurately. Return only the translation result, nothing else.",
    "customer_service": "你是一位专业、友好的智能客服助手。请耐心、礼貌地回答用户的问题，提供准确有用的信息。如果无法回答，请诚实告知并建议用户联系人工客服。回复使用中文。",
}


def _build_messages(db: Session, session_id: str, user_content: str, agent_type: str):
    logger.info(
        f"Building messages: session_id={session_id}, agent_type={agent_type}, content_length={len(user_content)}"
    )

    history = (
        db.query(ChatHistory)
        .filter(ChatHistory.session_id == session_id)
        .order_by(ChatHistory.created_at.asc())
        .all()
    )
    messages = [
        {"role": "system", "content": SYSTEM_PROMPTS.get(agent_type, SYSTEM_PROMPTS["chat"])}
    ]
    for h in history:
        messages.append({"role": h.role, "content": h.content})
    messages.append({"role": "user", "content": user_content})

    logger.info(
        f"Messages built: total_messages={len(messages)}, history_count={len(history)}"
    )
    return messages


async def get_llm_response(
    db: Session,
    agent_type: str,
    session_id: str,
    user_content: str,
    model_id: Optional[int] = None,
) -> str:
    logger.info(
        f"[LLM Call] Starting non-streaming request: session={session_id}, agent_type={agent_type}"
    )

    model, provider = resolve_model(db, agent_type, model_id)
    messages = _build_messages(db, session_id, user_content, agent_type)

    start_time = time.time()
    try:
        client = AsyncOpenAI(base_url=provider.api_base, api_key=provider.api_key)
        logger.info(
            f"[LLM Call] Sending request to {provider.api_base}, model={model.name}, messages_count={len(messages)}"
        )

        response = await client.chat.completions.create(
            model=model.name,
            messages=messages,
            max_tokens=model.max_tokens or 1048576,
            temperature=float(model.temperature) if model.temperature else 0.7,
        )

        elapsed = time.time() - start_time
        content = response.choices[0].message.content
        logger.info(
            f"[LLM Call] Response received: elapsed={elapsed:.2f}s, response_length={len(content)}, finish_reason={response.choices[0].finish_reason}"
        )
        return content
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"[LLM Call] Failed after {elapsed:.2f}s: {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=502, detail=f"AI 服务调用失败: {str(e)}"
        )


async def stream_llm_response(
    db: Session,
    agent_type: str,
    session_id: str,
    user_content: str,
    model_id: Optional[int] = None,
) -> AsyncGenerator[str, None]:
    logger.info(
        f"[LLM Stream] Starting streaming request: session={session_id}, agent_type={agent_type}"
    )

    model, provider = resolve_model(db, agent_type, model_id)
    messages = _build_messages(db, session_id, user_content, agent_type)

    start_time = time.time()
    chunk_count = 0
    try:
        client = AsyncOpenAI(base_url=provider.api_base, api_key=provider.api_key)
        logger.info(
            f"[LLM Stream] Sending streaming request to {provider.api_base}, model={model.name}, messages_count={len(messages)}"
        )

        stream = await client.chat.completions.create(
            model=model.name,
            messages=messages,
            max_tokens=model.max_tokens or 1048576,
            temperature=float(model.temperature) if model.temperature else 0.7,
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                chunk_count += 1
                yield delta.content

        elapsed = time.time() - start_time
        logger.info(
            f"[LLM Stream] Completed: elapsed={elapsed:.2f}s, chunks={chunk_count}"
        )
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(
            f"[LLM Stream] Failed after {elapsed:.2f}s, chunks_received={chunk_count}: {type(e).__name__}: {e}"
        )
        yield f"\n\n[错误] AI 服务调用失败: {str(e)}"
