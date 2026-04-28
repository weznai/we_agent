import json

from langchain_core.tools import tool as lc_tool

from ...utils.logger import get_logger
from ..registry import register
from .factory import create, list_models

logger = get_logger(__name__)


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
        generator = create(model=model or None)
        result = generator.generate(prompt=prompt, size=size, n=1)

        images = result.get("images", [])
        if not images:
            return json.dumps({"success": False, "message": "图片生成失败：无返回数据"}, ensure_ascii=False)

        img = images[0]
        return json.dumps({
            "success": True,
            "message": "图片生成成功",
            "url": img["url"],
            "filename": img["filename"],
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
    models = list_models()
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
