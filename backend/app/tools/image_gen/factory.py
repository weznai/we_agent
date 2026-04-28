import os
from typing import Optional

from ...utils.logger import get_logger

logger = get_logger(__name__)

_model_registry: dict[str, dict] = {}


def register_model(
    model_id: str,
    generator_cls: type,
    provider: str,
    name: str = "",
    description: str = "",
    api_key_field: str = "IMAGE_GEN_API_KEY",
):
    _model_registry[model_id] = {
        "cls": generator_cls,
        "provider": provider,
        "name": name or model_id,
        "description": description,
        "api_key_field": api_key_field,
    }
    logger.info(f"[ModelFactory] Registered model: {model_id} -> {provider}/{generator_cls.__name__}")


def create(model: Optional[str] = None, api_key: Optional[str] = None):
    """
    根据模型名称创建生成器实例。
    model 为空时使用系统默认模型。
    """
    from ...config import get_settings
    settings = get_settings()

    model_id = model or settings.IMAGE_GEN_MODEL
    if not model_id:
        model_id = "Kolors"

    entry = _model_registry.get(model_id)
    if not entry:
        available = ", ".join(sorted(_model_registry.keys())) or "none"
        raise ValueError(f"未找到模型: {model_id}，可用模型: {available}")

    if not api_key:
        api_key = getattr(settings, entry["api_key_field"], "") or settings.IMAGE_GEN_API_KEY

    return entry["cls"](api_key=api_key, model=model_id)


def list_models() -> list[dict]:
    return [
        {
            "id": mid,
            "name": info["name"],
            "provider": info["provider"],
            "description": info["description"],
        }
        for mid, info in _model_registry.items()
    ]


def get_model_info(model_id: str) -> Optional[dict]:
    return _model_registry.get(model_id)


def get_output_dir() -> str:
    from ...config import get_settings
    settings = get_settings()
    output_dir = settings.IMAGE_GEN_OUTPUT_DIR or os.path.join(settings.UPLOAD_DIR, "image_gen")
    os.makedirs(output_dir, exist_ok=True)
    return output_dir
