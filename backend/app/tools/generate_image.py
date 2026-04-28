import json
import base64
import datetime
import os

import httpx
from langchain_core.tools import tool as lc_tool

from ..utils.logger import get_logger
from ..config import get_settings
from .registry import register

logger = get_logger(__name__)

_SUPPORTED_MODELS = {
    "Kolors": {"provider": "gitee", "name": "Kolors", "description": "免费文生图模型（默认）"},
    "flux-schnell": {"provider": "gitee", "name": "Flux Schnell", "description": "快速生成"},
    "stable-diffusion": {"provider": "gitee", "name": "Stable Diffusion", "description": "经典艺术风格"},
}


def _get_output_dir() -> str:
    settings = get_settings()
    output_dir = settings.IMAGE_GEN_OUTPUT_DIR or os.path.join(settings.UPLOAD_DIR, "image_gen")
    os.makedirs(output_dir, exist_ok=True)
    return output_dir


def _make_filename(index: int = None) -> str:
    now = datetime.datetime.now()
    ts = now.strftime("%Y%m%d_%H%M%S")
    ms = f"{now.microsecond // 1000:03d}"
    suffix = f"_{index}" if index is not None else ""
    return f"img_{ts}_{ms}{suffix}.png"


def _generate_image(prompt: str, size: str = "1024x1024", model: str = "") -> dict:
    settings = get_settings()
    model_name = model or settings.IMAGE_GEN_MODEL or "Kolors"
    api_key = settings.IMAGE_GEN_API_KEY

    if not api_key:
        raise ValueError("IMAGE_GEN_API_KEY 未配置")
    if model_name not in _SUPPORTED_MODELS:
        available = ", ".join(sorted(_SUPPORTED_MODELS.keys()))
        raise ValueError(f"未找到模型: {model_name}，可用模型: {available}")

    url = "https://ai.gitee.com/v1/images/generations"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    payload = {
        "model": model_name,
        "prompt": prompt,
        "n": 1,
        "size": size,
        "response_format": "b64_json",
    }

    logger.info(f"[GiteeImageGen] Requesting: model={model_name}, size={size}, prompt={prompt[:100]}")

    resp = httpx.post(url, json=payload, headers=headers, timeout=120)
    if resp.status_code != 200:
        raise Exception(f"Gitee API 调用失败 ({resp.status_code}): {resp.text}")

    result = resp.json()
    if "data" not in result or len(result["data"]) == 0:
        raise Exception(f"Gitee API 返回数据格式错误: {result}")

    output_dir = _get_output_dir()
    filename = _make_filename()
    local_path = os.path.join(output_dir, filename)
    img_bytes = base64.b64decode(result["data"][0]["b64_json"])
    with open(local_path, "wb") as f:
        f.write(img_bytes)

    logger.info(f"[GiteeImageGen] Saved: {local_path}")

    return {
        "provider": "gitee",
        "model": model_name,
        "url": f"/uploads/image_gen/{filename}",
        "filename": filename,
    }


@lc_tool
def generate_image(prompt: str, size: str = "1024x1024", model: str = "") -> str:
    """生成图片。根据文字描述使用AI生成图片，默认使用Kolors免费模型。
    可通过model参数指定其他已注册的模型。生成完成后返回图片的访问地址。

    Args:
        prompt: 图片描述提示词，越详细效果越好，支持中英文
        size: 图片尺寸，默认 "1024x1024"
        model: 模型名称，为空使用系统默认模型。可用模型可通过 list_image_models 工具查询
    """
    logger.info(f"[Tool generate_image] Invoked: model={model or 'default'}, size={size}, prompt={prompt[:100]}")

    try:
        result = _generate_image(prompt=prompt, size=size, model=model)
        return json.dumps({
            "success": True,
            "message": "图片生成成功。请直接使用下面url字段的值作为markdown图片地址，格式：![图片描述](url的值)。不要修改url路径。",
            "url": result["url"],
            "filename": result["filename"],
            "provider": result["provider"],
            "model": result["model"],
        }, ensure_ascii=False)

    except ValueError as e:
        logger.error(f"[Tool generate_image] Config error: {e}")
        return json.dumps({"success": False, "message": str(e)}, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[Tool generate_image] Failed: {e}")
        return json.dumps({"success": False, "message": f"图片生成失败: {str(e)}"}, ensure_ascii=False)


@lc_tool
def list_image_models() -> str:
    """查询所有可用的图片生成模型列表。返回模型ID、名称、供应商和描述。
    在使用 generate_image 工具前可先调用此工具查看可用模型。

    Args: 无参数
    """
    models = [
        {"id": mid, "name": info["name"], "provider": info["provider"], "description": info["description"]}
        for mid, info in _SUPPORTED_MODELS.items()
    ]
    return json.dumps({"models": models}, ensure_ascii=False)


register(
    name="generate_image",
    tool=generate_image,
    description="根据文字描述使用AI生成图片（默认Kolors免费模型）",
    status_msg="正在生成图片...",
    agents=["*"],
)

register(
    name="list_image_models",
    tool=list_image_models,
    description="查询所有可用的图片生成模型",
    status_msg="正在查询可用模型...",
    agents=["*"],
)
