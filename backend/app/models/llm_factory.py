from typing import Optional
from dataclasses import dataclass

from ..utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class LLMConfig:
    model_name: str
    api_base: str
    api_key: str
    temperature: float = 0.7
    max_tokens: Optional[int] = None


_cached_config = None


def _get_yaml_config() -> dict:
    global _cached_config
    if _cached_config is not None:
        return _cached_config
    from ..services.config_loader import load_yaml_config
    _cached_config = load_yaml_config()
    return _cached_config


def resolve_llm_config(
    model_id: Optional[int] = None,
    agent_type: str = "chat",
) -> LLMConfig:
    if model_id:
        return _resolve_from_db(model_id)

    config = _get_yaml_config()
    if not config:
        raise ValueError("llm_config.yaml not found or empty")

    providers = {p["name"]: p for p in config.get("providers", [])}
    models = {}
    for m in config.get("models", []):
        p_name = m.get("provider", "")
        models[f"{p_name}/{m['name']}"] = m

    mappings = config.get("mappings", [])
    defaults = config.get("defaults", {})

    matching = [m for m in mappings if m.get("agent_type") == agent_type]
    if not matching:
        matching = [m for m in mappings if m.get("agent_type") == "chat"]
    if not matching:
        raise ValueError(f"no mapping for agent_type={agent_type}")

    matching.sort(key=lambda x: x.get("priority", 0), reverse=True)
    best = matching[0]
    model_key = f"{best.get('provider', '')}/{best.get('model', '')}"
    selected_model = models.get(model_key)
    if not selected_model:
        raise ValueError(f"mapped model '{model_key}' not found in config")

    provider_name = selected_model.get("provider", "")
    provider = providers.get(provider_name)
    if not provider:
        raise ValueError(f"provider '{provider_name}' not found")
    if not provider.get("api_base") or not provider.get("api_key"):
        raise ValueError(f"provider '{provider_name}' missing api_base or api_key")

    temperature = float(selected_model.get("temperature", defaults.get("temperature", "0.7")))
    max_tokens = selected_model.get("max_tokens", defaults.get("max_tokens"))

    logger.info(
        f"LLM config resolved from yaml: model={selected_model['name']}, "
        f"provider={provider_name}, api_base={provider['api_base']}"
    )

    return LLMConfig(
        model_name=selected_model["name"],
        api_base=provider["api_base"],
        api_key=provider["api_key"],
        temperature=temperature,
        max_tokens=max_tokens,
    )


def _resolve_from_db(model_id: int) -> LLMConfig:
    from ..database import SessionLocal
    from ..entities import Model, Provider

    db = SessionLocal()
    try:
        model = db.query(Model).filter(Model.id == model_id, Model.is_active == True).first()
        if not model:
            raise ValueError(f"model_id={model_id} not found or disabled")

        provider = db.query(Provider).filter(Provider.id == model.provider_id, Provider.is_active == True).first()
        if not provider:
            raise ValueError(f"provider not found for model_id={model_id}")
        if not provider.api_base or not provider.api_key:
            raise ValueError(f"provider '{provider.name}' missing api_base or api_key")

        logger.info(
            f"LLM config resolved from DB: model={model.name}, "
            f"provider={provider.name}, api_base={provider.api_base}"
        )

        return LLMConfig(
            model_name=model.name,
            api_base=provider.api_base,
            api_key=provider.api_key,
            temperature=float(model.temperature) if model.temperature else 0.7,
            max_tokens=model.max_tokens,
        )
    finally:
        db.close()
