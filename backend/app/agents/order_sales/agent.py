import time
from typing import Optional

from ..base import make_agent, stream_agent_response
from .skills import ALL_TOOLS
from .prompt import get_system_prompt
from ...utils.logger import get_logger

logger = get_logger(__name__)


def create_agent(db, model_id: Optional[int] = None):
    logger.info(f"Creating order_sales agent: model_id={model_id}")
    return make_agent(db, ALL_TOOLS, get_system_prompt(), model_id, agent_type="customer_service")


async def stream_response(db, session_id: str, user_content: str, model_id: Optional[int] = None):
    logger.info(f"[OrderSales] Starting stream: session={session_id}, content_length={len(user_content)}, model_id={model_id}")
    start_time = time.time()

    agent = create_agent(db, model_id)
    chunk_count = 0
    async for chunk in stream_agent_response(agent, session_id, user_content):
        chunk_count += 1
        yield chunk

    elapsed = time.time() - start_time
    logger.info(f"[OrderSales] Stream finished: session={session_id}, elapsed={elapsed:.2f}s, chunks={chunk_count}")
