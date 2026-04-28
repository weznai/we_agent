from typing import Optional, Tuple

from sqlalchemy.orm import Session
from fastapi import HTTPException

from ..entities import Model, ModelMapping, Provider
from ..utils.logger import get_logger

logger = get_logger(__name__)

CHAT_LIKE_TYPES = {"chat", "multimodal"}


def _is_chat_like(model: Model) -> bool:
    return model.model_type in CHAT_LIKE_TYPES


def resolve_model(
    db: Session,
    agent_type: str,
    model_id: Optional[int] = None,
) -> Tuple[Model, Provider]:
    logger.info(f"Resolving model: agent_type={agent_type}, model_id={model_id}")

    if model_id:
        model = db.query(Model).filter(
            Model.id == model_id, Model.is_active == True
        ).first()
        if not model:
            logger.error(f"Model not found or disabled: model_id={model_id}")
            raise HTTPException(
                status_code=400,
                detail=f"model not found or disabled (model_id={model_id})",
            )
    else:
        mapping = (
            db.query(ModelMapping)
            .filter(ModelMapping.agent_type == agent_type)
            .order_by(ModelMapping.priority.desc())
            .first()
        )
        if not mapping:
            mapping = (
                db.query(ModelMapping)
                .filter(ModelMapping.agent_type == "chat")
                .order_by(ModelMapping.priority.desc())
                .first()
            )
        if not mapping:
            logger.error(
                f"No model mapping found for agent_type={agent_type} or fallback 'chat'"
            )
            raise HTTPException(
                status_code=400,
                detail=f"no model mapping for agent_type={agent_type}",
            )
        model = db.query(Model).filter(
            Model.id == mapping.model_id, Model.is_active == True
        ).first()
        if not model:
            logger.error(f"Mapped model not found or disabled: model_id={mapping.model_id}")
            raise HTTPException(
                status_code=400,
                detail=f"model not found or disabled (model_id={mapping.model_id})",
            )

    provider = db.query(Provider).filter(
        Provider.id == model.provider_id, Provider.is_active == True
    ).first()
    if not provider:
        logger.error(f"Provider not found or disabled: provider_id={model.provider_id}")
        raise HTTPException(
            status_code=400,
            detail=f"provider not found or disabled (provider_id={model.provider_id})",
        )

    if not provider.api_base or not provider.api_key:
        logger.error(
            f"Provider missing api_base or api_key: provider={provider.display_name or provider.name}"
        )
        raise HTTPException(
            status_code=400,
            detail=f"provider {provider.display_name or provider.name} missing api_base or api_key",
        )

    logger.info(
        f"Model resolved: model={model.name}, provider={provider.name}, api_base={provider.api_base}"
    )
    return model, provider
