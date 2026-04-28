import time
from typing import Optional

from ..base import make_agent, stream_agent_response
from .prompt import get_system_prompt
from ...tools import get_tools
from ...utils.logger import get_logger

logger = get_logger(__name__)

AGENT_TYPE = "smart_measurement"


def create_agent(db, user_id: int = None, model_id: Optional[int] = None, knowledge_group_id: Optional[int] = None):
    logger.info(f"Creating smart_measurement agent: model_id={model_id}, user_id={user_id}")

    tools = get_tools(AGENT_TYPE)
    prompt = get_system_prompt()
    return make_agent(db, tools, prompt, model_id, agent_type=AGENT_TYPE)


async def stream_response(db, session_id: str, user_content: str, user_id: int = None, model_id: Optional[int] = None, knowledge_group_id: Optional[int] = None):
    logger.info(f"[SmartMeasurement] Starting stream: session={session_id}, content_length={len(user_content)}, model_id={model_id}")
    start_time = time.time()

    agent = create_agent(db, user_id=user_id, model_id=model_id, knowledge_group_id=knowledge_group_id)
    chunk_count = 0
    async for chunk in stream_agent_response(agent, session_id, user_content):
        chunk_count += 1
        yield chunk

    elapsed = time.time() - start_time
    logger.info(f"[SmartMeasurement] Stream finished: session={session_id}, elapsed={elapsed:.2f}s, chunks={chunk_count}")
