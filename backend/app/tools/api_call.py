import json
import time
from pathlib import Path
from typing import Optional

import httpx
from langchain_core.tools import tool as lc_tool

from ..utils.logger import get_logger
from ..config import get_settings
from .registry import register

logger = get_logger(__name__)

SKILL_FILE = Path(__file__).resolve().parent.parent / "skills" / "order_sales_management.md"


def _get_api_config() -> tuple[str, dict]:
    try:
        settings = get_settings()
        base_url = settings.ORDER_API_BASE_URL
        headers = {"Content-Type": "application/json", "X-API-Key": settings.ORDER_API_KEY}
        logger.debug(f"API config loaded: base_url={base_url}")
        return base_url, headers
    except Exception as e:
        logger.warning(f"Failed to load API config, using defaults: {e}")
        return "http://121.43.198.13:8080", {"Content-Type": "application/json"}


def _call_api(method: str, path: str, body: dict = None) -> dict:
    base_url, headers = _get_api_config()
    url = f"{base_url}{path}"
    start_time = time.time()

    logger.info(f"[External API] >>> {method} {url}, body={json.dumps(body, ensure_ascii=False) if body else 'None'}")

    try:
        with httpx.Client(timeout=30.0, follow_redirects=True) as client:
            if method.upper() == "GET":
                resp = client.get(url, params=body, headers=headers)
            elif method.upper() == "DELETE":
                resp = client.request("DELETE", url, json=body, headers=headers)
            elif method.upper() == "PUT":
                resp = client.put(url, json=body, headers=headers)
            else:
                resp = client.post(url, json=body, headers=headers)

            elapsed = time.time() - start_time

            if resp.status_code == 200:
                result = resp.json() if resp.text else {"success": True}
                logger.info(f"[External API] <<< {method} {path} | status=200 | elapsed={elapsed:.2f}s | response_length={len(resp.text)}")
                logger.debug(f"[External API] <<< Response preview: {str(result)[:500]}")
                if isinstance(result, (bool, type(None))) or not isinstance(result, dict):
                    result = {"success": True, "data": result}
                result["_status"] = 200
                return result
            else:
                logger.error(f"[External API] <<< {method} {path} | status={resp.status_code} | elapsed={elapsed:.2f}s | detail={resp.text[:500]}")
                return {"error": f"API返回错误: {resp.status_code}", "detail": resp.text}
    except httpx.TimeoutException as e:
        elapsed = time.time() - start_time
        logger.error(f"[External API] <<< {method} {path} | TIMEOUT after {elapsed:.2f}s: {e}")
        return {"error": f"API调用超时(30s): {str(e)}"}
    except httpx.ConnectError as e:
        elapsed = time.time() - start_time
        logger.error(f"[External API] <<< {method} {path} | CONNECTION FAILED after {elapsed:.2f}s: {e}")
        return {"error": f"API连接失败: {str(e)}"}
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"[External API] <<< {method} {path} | ERROR after {elapsed:.2f}s: {type(e).__name__}: {e}")
        return {"error": f"API调用失败: {str(e)}"}


def get_skill_content() -> str:
    if SKILL_FILE.exists():
        return SKILL_FILE.read_text(encoding="utf-8")
    logger.warning(f"Skill file not found: {SKILL_FILE}")
    return ""


MAX_TOOL_RESPONSE_CHARS = 30000

_LIST_FIELD_SHORT_NAMES = {
    "orderId": "id",
    "productId": "pid",
    "supplierId": "sid",
    "orderRegion": "region",
    "orderTime": "time",
    "quantity": "qty",
    "amount": "amt",
    "status": "st",
    "name": "n",
    "description": "desc",
    "price": "p",
    "quantityInStock": "stock",
    "phone": "ph",
    "address": "addr",
    "deliveryAreas": "areas",
    "rating": "rt",
    "substituteProductId": "subId",
    "substituteName": "subName",
}

_SHORT_TO_ORIG = {v: k for k, v in _LIST_FIELD_SHORT_NAMES.items()}


def _compact_item(item: dict) -> dict:
    return {_LIST_FIELD_SHORT_NAMES.get(k, k): v for k, v in item.items()}


def _optimize_response(result: dict) -> dict:
    if "error" in result:
        return result
    data = result.get("data")
    if not isinstance(data, list) or len(data) == 0:
        return result
    compacted = [_compact_item(item) for item in data]
    optimized = {
        "ok": result.get("success", True),
        "d": compacted,
        "_keys": {k: v for k, v in _SHORT_TO_ORIG.items() if any(k in c for c in compacted)},
        "_total": len(data),
    }
    return optimized


def _truncate_response(result: dict) -> dict:
    text = json.dumps(result, ensure_ascii=False)
    if len(text) <= MAX_TOOL_RESPONSE_CHARS:
        return result

    total = len(text)
    data = result.get("data") or result.get("d")

    if isinstance(data, list) and len(data) > 0:
        kept = []
        length = 0
        for item in data:
            chunk = json.dumps(item, ensure_ascii=False)
            if length + len(chunk) + 300 > MAX_TOOL_RESPONSE_CHARS:
                break
            kept.append(item)
            length += len(chunk) + 2
        remaining = len(data) - len(kept)
        summary = {
            "ok": result.get("success") or result.get("ok", True),
            "d": kept,
            "_keys": result.get("_keys", {}),
            "_total": result.get("_total", len(data)),
            "_shown": len(kept),
            "_remaining": remaining,
            "_hint": f"共{len(data)}条记录，已展示前{len(kept)}条。如需查看更多，请使用分页或筛选条件缩小查询范围。",
        }
        logger.info(
            f"[Tool api_call] Response truncated: total={total} chars, "
            f"kept={len(kept)}/{len(data)} items, remaining={remaining}"
        )
        return summary

    return {
        "ok": result.get("success") or result.get("ok", True),
        "d": text[: MAX_TOOL_RESPONSE_CHARS // 2] + "\n...[截断]...",
        "_total": total,
        "_hint": f"返回数据过大({total}字符)已截断。请使用筛选条件缩小查询范围。",
    }


@lc_tool
def api_call(method: str, path: str, body: str = None) -> str:
    """调用订单销售管理系统的API接口。根据技能文档中的接口说明，传入对应的HTTP方法、路径和JSON参数。

    Args:
        method: HTTP方法，如 GET、POST、PUT、DELETE
        path: API路径，如 /orders/createOrder、/products/getProductById
        body: JSON格式的请求参数字符串，如 '{"orderId": 1}'
    """
    logger.info(f"[Tool api_call] Invoked: method={method}, path={path}, body={body}")

    parsed_body = None
    if body:
        try:
            parsed_body = json.loads(body)
        except json.JSONDecodeError:
            logger.error(f"[Tool api_call] Invalid JSON body: {body}")
            return json.dumps({"error": "body必须是有效的JSON字符串"}, ensure_ascii=False)

    result = _call_api(method, path, parsed_body)
    logger.info(f"[Tool api_call] Result: error={bool(result.get('error'))}, keys={list(result.keys())}")

    result = _optimize_response(result)
    result = _truncate_response(result)
    return json.dumps(result, ensure_ascii=False, separators=(",", ":"))


register(
    name="api_call",
    tool=api_call,
    description="调用订单销售管理系统API接口",
    status_msg="正在查询订单信息...",
    agents=["customer_service"],
)
