import base64
import time
from typing import AsyncGenerator, Optional, List

from openai import AsyncOpenAI
from sqlalchemy.orm import Session
from fastapi import HTTPException

from ..entities import ChatHistory
from ..services.model_service import resolve_model
from ..utils.logger import get_logger

logger = get_logger(__name__)

SYSTEM_PROMPTS = {
    "chat": "You are a helpful, knowledgeable AI assistant. Respond in the same language the user uses. Be concise and accurate.",
    "multimodal": "You are a helpful, knowledgeable AI assistant with vision capabilities. You can analyze and describe images. Respond in the same language the user uses. Be concise and accurate.",
    "translation": "You are a professional translator. Translate the given text accurately. Return only the translation result, nothing else.",
    "customer_service": "你是一位专业、友好的智能客服助手。请耐心、礼貌地回答用户的问题，提供准确有用的信息。如果无法回答，请诚实告知并建议用户联系人工客服。回复使用中文。",
    "smart_assistant": "你是一个全能的智能助手，能够帮助用户解答各种问题、分析数据、撰写文案、编程辅助、知识查询等。中文回复，专业友好简洁。",
    "smart_measurement": "你是一个专业的智能测量助手，擅长各类测量相关的计算、分析、方案设计和问题解答。中文回复，计算过程清晰展示步骤，结果附带单位和精度说明。",
}


def _build_text_content(content: str) -> dict:
    return {"type": "text", "text": content}


def _build_image_content(image_url: str) -> dict:
    if image_url.startswith("data:"):
        return {"type": "image_url", "image_url": {"url": image_url}}
    if image_url.startswith("http://") or image_url.startswith("https://"):
        return {"type": "image_url", "image_url": {"url": image_url}}
    return {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_url}"}}


def _build_messages(
    db: Session,
    session_id: str,
    user_content: str,
    agent_type: str,
    images: Optional[List[str]] = None,
):
    logger.info(
        f"Building messages: session_id={session_id}, agent_type={agent_type}, "
        f"content_length={len(user_content)}, images={len(images) if images else 0}"
    )

    history = (
        db.query(ChatHistory)
        .filter(ChatHistory.session_id == session_id)
        .order_by(ChatHistory.created_at.asc())
        .all()
    )
    system_prompt = SYSTEM_PROMPTS.get(agent_type, SYSTEM_PROMPTS["chat"])
    messages = [{"role": "system", "content": system_prompt}]

    for h in history:
        messages.append({"role": h.role, "content": h.content})

    if images:
        user_msg_content = [_build_text_content(user_content)]
        for img in images:
            user_msg_content.append(_build_image_content(img))
        messages.append({"role": "user", "content": user_msg_content})
    else:
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
    images: Optional[List[str]] = None,
) -> str:
    logger.info(
        f"[LLM Call] Starting non-streaming request: session={session_id}, agent_type={agent_type}, images={len(images) if images else 0}"
    )

    model, provider = resolve_model(db, agent_type, model_id)
    messages = _build_messages(db, session_id, user_content, agent_type, images)

    start_time = time.time()
    try:
        client = AsyncOpenAI(base_url=provider.api_base, api_key=provider.api_key)
        logger.info(
            f"[LLM Call] Sending request to {provider.api_base}, model={model.name}, messages_count={len(messages)}"
        )

        kwargs = dict(
            model=model.name,
            messages=messages,
            temperature=float(model.temperature) if model.temperature else 0.7,
        )
        if model.max_tokens:
            kwargs["max_tokens"] = max(1, min(model.max_tokens, 393216))

        response = await client.chat.completions.create(**kwargs)

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
    images: Optional[List[str]] = None,
) -> AsyncGenerator[str, None]:
    logger.info(
        f"[LLM Stream] Starting streaming request: session={session_id}, agent_type={agent_type}, images={len(images) if images else 0}"
    )

    model, provider = resolve_model(db, agent_type, model_id)
    messages = _build_messages(db, session_id, user_content, agent_type, images)

    start_time = time.time()
    chunk_count = 0
    reasoning_parts = []
    try:
        client = AsyncOpenAI(base_url=provider.api_base, api_key=provider.api_key)
        logger.info(
            f"[LLM Stream] Sending streaming request to {provider.api_base}, model={model.name}, messages_count={len(messages)}"
        )

        kwargs = dict(
            model=model.name,
            messages=messages,
            temperature=float(model.temperature) if model.temperature else 0.7,
            stream=True,
        )
        if model.max_tokens:
            kwargs["max_tokens"] = max(1, min(model.max_tokens, 393216))

        stream = await client.chat.completions.create(**kwargs)
        async for chunk in stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            if delta.content:
                chunk_count += 1
                yield delta.content
            rc = getattr(delta, 'reasoning_content', None)
            if rc:
                reasoning_parts.append(rc)

        elapsed = time.time() - start_time
        full_reasoning = "".join(reasoning_parts) if reasoning_parts else None
        logger.info(
            f"[LLM Stream] Completed: elapsed={elapsed:.2f}s, chunks={chunk_count}, has_reasoning={full_reasoning is not None}"
        )
        yield {"__meta__": {"reasoning_content": full_reasoning}}
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(
            f"[LLM Stream] Failed after {elapsed:.2f}s, chunks_received={chunk_count}: {type(e).__name__}: {e}"
        )
        yield f"\n\n[错误] AI 服务调用失败: {str(e)}"
