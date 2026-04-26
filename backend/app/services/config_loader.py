import os
import re
from pathlib import Path

import yaml
from sqlalchemy.orm import Session

from ..entities import Provider, Model, ModelMapping
from ..utils.logger import get_logger

logger = get_logger(__name__)

_CONFIG_DIR = Path(__file__).resolve().parent.parent.parent
_CONFIG_FILE = _CONFIG_DIR / "llm_config.yaml"

_ENV_VAR_PATTERN = re.compile(r"\$\{([^}]+)\}")


def _resolve_env(value: str) -> str:
    def _replacer(match):
        var_name = match.group(1)
        resolved = os.environ.get(var_name, "")
        if not resolved:
            logger.warning(f"Environment variable not set: {var_name}")
        return resolved

    return _ENV_VAR_PATTERN.sub(_replacer, value)


def _resolve_value(value):
    if isinstance(value, str):
        return _resolve_env(value)
    if isinstance(value, dict):
        return {k: _resolve_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_resolve_value(item) for item in value]
    return value


def load_yaml_config(config_path: str | Path | None = None) -> dict | None:
    path = Path(config_path) if config_path else _CONFIG_FILE
    if not path.exists():
        logger.info(f"LLM config file not found: {path}, skipping sync")
        return None
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    if not raw:
        return None
    return _resolve_value(raw)


def sync_config_to_db(db: Session, config: dict) -> None:
    defaults = config.get("defaults", {})

    provider_name_to_id = _sync_providers(db, config.get("providers", []))
    model_key_to_id = _sync_models(
        db, config.get("models", []), provider_name_to_id, defaults
    )
    _sync_mappings(db, config.get("mappings", []), provider_name_to_id, model_key_to_id)

    db.commit()
    logger.info("LLM config sync complete")


def _sync_providers(db: Session, providers_cfg: list[dict]) -> dict[str, int]:
    name_to_id: dict[str, int] = {}
    for cfg in providers_cfg:
        name = cfg["name"]
        existing: Provider | None = db.query(Provider).filter(Provider.name == name).first()
        if existing:
            _update_provider(existing, cfg)
            db.add(existing)
            name_to_id[name] = existing.id
            logger.debug(f"Provider updated: {name}")
        else:
            provider = Provider(
                name=name,
                display_name=cfg.get("display_name", ""),
                description=cfg.get("description", ""),
                api_base=cfg.get("api_base", ""),
                api_key=cfg.get("api_key", ""),
                logo=cfg.get("logo", ""),
                is_active=cfg.get("is_active", True),
            )
            db.add(provider)
            db.flush()
            name_to_id[name] = provider.id
            logger.info(f"Provider created: {name}")
    return name_to_id


def _update_provider(provider: Provider, cfg: dict) -> None:
    if "display_name" in cfg:
        provider.display_name = cfg["display_name"]
    if "description" in cfg:
        provider.description = cfg["description"]
    if "api_base" in cfg:
        provider.api_base = cfg["api_base"]
    if "api_key" in cfg and cfg["api_key"]:
        provider.api_key = cfg["api_key"]
    if "logo" in cfg:
        provider.logo = cfg["logo"]
    if "is_active" in cfg:
        provider.is_active = cfg["is_active"]


def _sync_models(
    db: Session,
    models_cfg: list[dict],
    provider_name_to_id: dict[str, int],
    defaults: dict,
) -> dict[str, int]:
    key_to_id: dict[str, int] = {}
    for cfg in models_cfg:
        provider_name = cfg.get("provider", "")
        provider_id = provider_name_to_id.get(provider_name)
        if provider_id is None:
            logger.warning(f"Model '{cfg.get('name')}' references unknown provider '{provider_name}', skipping")
            continue

        model_name = cfg["name"]
        existing: Model | None = db.query(Model).filter(
            Model.name == model_name,
            Model.provider_id == provider_id,
        ).first()

        if existing:
            _update_model(existing, cfg, defaults)
            db.add(existing)
            key_to_id[f"{provider_name}/{model_name}"] = existing.id
            logger.debug(f"Model updated: {provider_name}/{model_name}")
        else:
            model = Model(
                provider_id=provider_id,
                name=model_name,
                display_name=cfg.get("display_name", ""),
                model_type=cfg.get("model_type", defaults.get("model_type", "chat")),
                description=cfg.get("description", ""),
                max_tokens=cfg.get("max_tokens", defaults.get("max_tokens", 1048576)),
                temperature=str(cfg.get("temperature", defaults.get("temperature", "0.7"))),
                embedding_dimension=cfg.get("embedding_dimension", 0),
                model_path=cfg.get("model_path", ""),
                is_active=cfg.get("is_active", defaults.get("is_active", True)),
            )
            db.add(model)
            db.flush()
            key_to_id[f"{provider_name}/{model_name}"] = model.id
            logger.info(f"Model created: {provider_name}/{model_name}")
    return key_to_id


def _update_model(model: Model, cfg: dict, defaults: dict) -> None:
    if "display_name" in cfg:
        model.display_name = cfg["display_name"]
    if "model_type" in cfg:
        model.model_type = cfg["model_type"]
    if "description" in cfg:
        model.description = cfg["description"]
    if "max_tokens" in cfg:
        model.max_tokens = cfg["max_tokens"]
    if "temperature" in cfg:
        model.temperature = str(cfg["temperature"])
    if "embedding_dimension" in cfg:
        model.embedding_dimension = cfg["embedding_dimension"]
    if "model_path" in cfg:
        model.model_path = cfg["model_path"]
    if "is_active" in cfg:
        model.is_active = cfg["is_active"]


def _sync_mappings(
    db: Session,
    mappings_cfg: list[dict],
    provider_name_to_id: dict[str, int],
    model_key_to_id: dict[str, int],
) -> None:
    for cfg in mappings_cfg:
        agent_type = cfg["agent_type"]
        provider_name = cfg.get("provider", "")
        model_name = cfg.get("model", "")
        model_key = f"{provider_name}/{model_name}"
        model_id = model_key_to_id.get(model_key)
        if model_id is None:
            logger.warning(f"Mapping for agent_type='{agent_type}' references unknown model '{model_key}', skipping")
            continue

        priority = cfg.get("priority", 0)

        existing: ModelMapping | None = db.query(ModelMapping).filter(
            ModelMapping.agent_type == agent_type,
            ModelMapping.model_id == model_id,
        ).first()

        if existing:
            existing.priority = priority
            db.add(existing)
            logger.debug(f"Mapping updated: {agent_type} -> {model_key}")
        else:
            mapping = ModelMapping(
                agent_type=agent_type,
                model_id=model_id,
                priority=priority,
            )
            db.add(mapping)
            db.flush()
            logger.info(f"Mapping created: {agent_type} -> {model_key}")
