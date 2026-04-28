import time
from typing import Optional

from ..base import make_agent, stream_agent_response
from .skills import create_knowledge_search_tool
from .prompt import get_system_prompt
from ...tools import get_tools
from ...utils.logger import get_logger

logger = get_logger(__name__)

AGENT_TYPE = "customer_service"


def create_agent(db, user_id: int = None, model_id: Optional[int] = None, knowledge_group_id: Optional[int] = None):
    logger.info(f"Creating order_sales agent: model_id={model_id}, user_id={user_id}, knowledge_group_id={knowledge_group_id}")

    tools = get_tools(AGENT_TYPE)
    if user_id is not None:
        try:
            tools.append(create_knowledge_search_tool(user_id, knowledge_group_id))
            logger.info("Knowledge search tool added to agent")
        except Exception as e:
            logger.warning(f"Failed to add knowledge search tool: {e}")

    prompt = get_system_prompt(with_knowledge=user_id is not None)
    return make_agent(db, tools, prompt, model_id, agent_type=AGENT_TYPE)


async def stream_response(db, session_id: str, user_content: str, user_id: int = None, model_id: Optional[int] = None, knowledge_group_id: Optional[int] = None):
    logger.info(f"[OrderSales] Starting stream: session={session_id}, content_length={len(user_content)}, model_id={model_id}")
    start_time = time.time()

    agent = create_agent(db, user_id=user_id, model_id=model_id, knowledge_group_id=knowledge_group_id)
    chunk_count = 0
    async for chunk in stream_agent_response(agent, session_id, user_content):
        chunk_count += 1
        yield chunk

    elapsed = time.time() - start_time
    logger.info(f"[OrderSales] Stream finished: session={session_id}, elapsed={elapsed:.2f}s, chunks={chunk_count}")
