import time
from typing import Optional

from ..base import make_agent, stream_agent_response
from .prompt import get_system_prompt
from ...tools import get_tools
from ...utils.logger import get_logger

logger = get_logger(__name__)

AGENT_TYPE = "smart_measurement"


def create_agent(model_id: Optional[int] = None, **kwargs):
    logger.info(f"Creating smart_measurement agent: model_id={model_id}")

    tools = get_tools(AGENT_TYPE)
    prompt = get_system_prompt()
    return make_agent(tools, prompt, model_id, agent_type=AGENT_TYPE)


async def stream_response(session_id: str, user_content: str, model_id: Optional[int] = None, **kwargs):
    logger.info(f"[SmartMeasurement] Starting stream: session={session_id}, content_length={len(user_content)}, model_id={model_id}")
    start_time = time.time()

    agent = create_agent(model_id=model_id)
    chunk_count = 0
    async for chunk in stream_agent_response(agent, session_id, user_content):
        chunk_count += 1
        yield chunk

    elapsed = time.time() - start_time
    logger.info(f"[SmartMeasurement] Stream finished: session={session_id}, elapsed={elapsed:.2f}s, chunks={chunk_count}")
