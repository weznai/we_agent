import base64
import datetime
import os

import httpx

from ...utils.logger import get_logger
from .factory import register_model, get_output_dir

logger = get_logger(__name__)


class GiteeImageGenerator:
    PROVIDER_NAME = "Gitee AI"
    BASE_URL = "https://ai.gitee.com/v1"

    def __init__(self, api_key: str, model: str = None):
        self.api_key = api_key
        self.model = model or "Kolors"
        if not self.api_key:
            raise ValueError("IMAGE_GEN_API_KEY 未配置")

    def generate(self, prompt: str, size: str = "1024x1024", n: int = 1) -> dict:
        url = f"{self.BASE_URL}/images/generations"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        payload = {
            "model": self.model,
            "prompt": prompt,
            "n": n,
            "size": size,
            "response_format": "b64_json",
        }

        logger.info(f"[GiteeImageGen] Requesting: model={self.model}, size={size}, prompt={prompt[:100]}")

        resp = httpx.post(url, json=payload, headers=headers, timeout=120)
        if resp.status_code != 200:
            raise Exception(f"Gitee API 调用失败 ({resp.status_code}): {resp.text}")

        result = resp.json()
        if "data" not in result or len(result["data"]) == 0:
            raise Exception(f"Gitee API 返回数据格式错误: {result}")

        output_dir = get_output_dir()
        saved = []
        for i, item in enumerate(result["data"]):
            filename = _make_filename(i if n > 1 else None)
            local_path = os.path.join(output_dir, filename)
            img_bytes = base64.b64decode(item["b64_json"])
            with open(local_path, "wb") as f:
                f.write(img_bytes)
            saved.append({
                "filename": filename,
                "local_path": local_path,
                "url": f"/uploads/image_gen/{filename}",
            })
            logger.info(f"[GiteeImageGen] Saved: {local_path}")

        return {
            "provider": "gitee",
            "model": self.model,
            "images": saved,
        }


def _make_filename(index: int = None) -> str:
    now = datetime.datetime.now()
    ts = now.strftime("%Y%m%d_%H%M%S")
    ms = f"{now.microsecond // 1000:03d}"
    suffix = f"_{index}" if index is not None else ""
    return f"img_{ts}_{ms}{suffix}.png"


register_model("Kolors", GiteeImageGenerator, provider="gitee", name="Kolors", description="免费文生图模型（默认）")
register_model("flux-schnell", GiteeImageGenerator, provider="gitee", name="Flux Schnell", description="快速生成")
register_model("stable-diffusion", GiteeImageGenerator, provider="gitee", name="Stable Diffusion", description="经典艺术风格")
