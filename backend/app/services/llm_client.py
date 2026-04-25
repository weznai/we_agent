import logging
from typing import AsyncGenerator, Optional
from openai import AsyncOpenAI
from sqlalchemy.orm import Session
from fastapi import HTTPException
from ..models.model_mapping import ModelMapping
from ..models.model import Model
from ..models.provider import Provider
from ..models.chat_history import ChatHistory

logger = logging.getLogger(__name__)

SYSTEM_PROMPTS = {
    "chat": "You are a helpful, knowledgeable AI assistant. Respond in the same language the user uses. Be concise and accurate.",
    "translation": "You are a professional translator. Translate the given text accurately. Return only the translation result, nothing else.",
    "customer_service": "你是一位专业、友好的智能客服助手。请耐心、礼貌地回答用户的问题，提供准确有用的信息。如果无法回答，请诚实告知并建议用户联系人工客服。回复使用中文。",
}


def _resolve_model(db: Session, agent_type: str, model_id: Optional[int] = None):
    if model_id:
        model = db.query(Model).filter(Model.id == model_id, Model.is_active == True).first()
        if not model:
            raise HTTPException(status_code=400, detail=f"模型不存在或已禁用 (model_id={model_id})")
    else:
        mapping = (
            db.query(ModelMapping)
            .filter(ModelMapping.agent_type == agent_type)
            .order_by(ModelMapping.priority.desc())
            .first()
        )
        if not mapping:
            raise HTTPException(status_code=400, detail=f"未配置 {agent_type} 类型的模型映射，请在系统管理中配置。")

        model = db.query(Model).filter(Model.id == mapping.model_id, Model.is_active == True).first()
        if not model:
            raise HTTPException(status_code=400, detail=f"模型不存在或已禁用 (model_id={mapping.model_id})")

    provider = db.query(Provider).filter(Provider.id == model.provider_id, Provider.is_active == True).first()
    if not provider:
        raise HTTPException(status_code=400, detail=f"供应商不存在或已禁用 (provider_id={model.provider_id})")

    if not provider.api_base or not provider.api_key:
        raise HTTPException(status_code=400, detail=f"供应商 {provider.display_name or provider.name} 未配置 API Base 或 API Key")

    return model, provider


def _build_messages(db: Session, session_id: str, user_content: str, agent_type: str):
    history = (
        db.query(ChatHistory)
        .filter(ChatHistory.session_id == session_id)
        .order_by(ChatHistory.created_at.asc())
        .all()
    )
    messages = [{"role": "system", "content": SYSTEM_PROMPTS.get(agent_type, SYSTEM_PROMPTS["chat"])}]
    for h in history:
        messages.append({"role": h.role, "content": h.content})
    messages.append({"role": "user", "content": user_content})
    return messages


async def get_llm_response(db: Session, agent_type: str, session_id: str, user_content: str, model_id: Optional[int] = None) -> str:
    model, provider = _resolve_model(db, agent_type, model_id)
    messages = _build_messages(db, session_id, user_content, agent_type)

    try:
        client = AsyncOpenAI(base_url=provider.api_base, api_key=provider.api_key)
        response = await client.chat.completions.create(
            model=model.name,
            messages=messages,
            max_tokens=model.max_tokens or 4096,
            temperature=float(model.temperature) if model.temperature else 0.7,
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"LLM API error: {e}")
        raise HTTPException(status_code=502, detail=f"AI 服务调用失败: {str(e)}")


async def stream_llm_response(db: Session, agent_type: str, session_id: str, user_content: str, model_id: Optional[int] = None) -> AsyncGenerator[str, None]:
    model, provider = _resolve_model(db, agent_type, model_id)
    messages = _build_messages(db, session_id, user_content, agent_type)

    try:
        client = AsyncOpenAI(base_url=provider.api_base, api_key=provider.api_key)
        stream = await client.chat.completions.create(
            model=model.name,
            messages=messages,
            max_tokens=model.max_tokens or 4096,
            temperature=float(model.temperature) if model.temperature else 0.7,
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                yield delta.content
    except Exception as e:
        logger.error(f"LLM streaming error: {e}")
        yield f"\n\n[错误] AI 服务调用失败: {str(e)}"
