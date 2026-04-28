from ..utils.logger import get_logger

logger = get_logger(__name__)

_registry: dict[str, dict] = {}


def register(
    name: str,
    tool,
    description: str = "",
    status_msg: str = "",
    agents: list[str] | None = None,
):
    _registry[name] = {
        "tool": tool,
        "name": name,
        "description": description,
        "status_msg": status_msg or f"正在执行工具 {name}...",
        "agents": agents or ["*"],
    }
    logger.info(f"[ToolRegistry] Registered tool: name={name}, agents={_registry[name]['agents']}")


def unregister(name: str):
    if name in _registry:
        del _registry[name]
        logger.info(f"[ToolRegistry] Unregistered tool: name={name}")


def get_tools(agent_type: str | None = None) -> list:
    result = []
    for entry in _registry.values():
        if agent_type is None or "*" in entry["agents"] or agent_type in entry["agents"]:
            result.append(entry["tool"])
    logger.debug(f"[ToolRegistry] get_tools(agent_type={agent_type}) -> {len(result)} tools")
    return result


def get_status_map() -> dict[str, str]:
    return {name: entry["status_msg"] for name, entry in _registry.items()}


def list_tools() -> list[dict]:
    return [
        {
            "name": name,
            "description": entry["description"],
            "status_msg": entry["status_msg"],
            "agents": entry["agents"],
        }
        for name, entry in _registry.items()
    ]
