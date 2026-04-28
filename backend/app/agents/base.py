import json
import time
from typing import Optional, Any, cast
from collections.abc import Mapping, Iterator

from langchain_openai import ChatOpenAI
from langchain_core.messages import (
    AIMessage,
    AIMessageChunk,
    HumanMessage,
    BaseMessage,
    BaseMessageChunk,
    ToolMessage,
    RemoveMessage,
)
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.message import REMOVE_ALL_MESSAGES

from ..models.llm_factory import resolve_llm_config
from ..utils.logger import get_logger

logger = get_logger(__name__)


def _patch_langchain_openai_for_reasoning():
    import langchain_openai.chat_models.base as _lc_base

    _orig_convert_delta = _lc_base._convert_delta_to_message_chunk
    _orig_convert_msg = _lc_base._convert_message_to_dict

    def _patched_convert_delta(
        _dict: Mapping[str, Any], default_class: type[BaseMessageChunk]
    ) -> BaseMessageChunk:
        msg = _orig_convert_delta(_dict, default_class)
        rc = _dict.get("reasoning_content")
        if rc and isinstance(msg, AIMessageChunk):
            msg.additional_kwargs["reasoning_content"] = rc
        return msg

    def _patched_convert_msg(message: BaseMessage, *args, **kwargs) -> dict:
        result = _orig_convert_msg(message, *args, **kwargs)
        if isinstance(message, AIMessage):
            rc = message.additional_kwargs.get("reasoning_content")
            if rc is not None:
                result["reasoning_content"] = rc
        return result

    _lc_base._convert_delta_to_message_chunk = _patched_convert_delta
    _lc_base._convert_message_to_dict = _patched_convert_msg
    logger.info(
        "Patched langchain_openai to preserve reasoning_content for thinking-mode models"
    )


_patch_langchain_openai_for_reasoning()

_memory_store = MemorySaver()


def build_llm(model_id=None, agent_type="chat"):
    cfg = resolve_llm_config(model_id=model_id, agent_type=agent_type)
    logger.info(
        f"Building LLM: model={cfg.model_name}, temperature={cfg.temperature}, max_tokens={cfg.max_tokens}"
    )
    kwargs = dict(
        model=cfg.model_name,
        openai_api_base=cfg.api_base,
        openai_api_key=cfg.api_key,
        temperature=cfg.temperature,
        streaming=True,
    )
    if cfg.max_tokens:
        kwargs["max_tokens"] = cfg.max_tokens
    return ChatOpenAI(**kwargs)


def _sanitize_messages(messages):
    tool_response_ids = {
        m.tool_call_id for m in messages if isinstance(m, ToolMessage)
    }
    tool_call_ids_in_ai = set()
    for m in messages:
        if isinstance(m, AIMessage) and m.tool_calls:
            for tc in m.tool_calls:
                tool_call_ids_in_ai.add(tc["id"])

    sanitized = []
    for m in messages:
        if isinstance(m, AIMessage) and m.tool_calls:
            valid = [tc for tc in m.tool_calls if tc["id"] in tool_response_ids]
            if valid:
                if len(valid) == len(m.tool_calls):
                    sanitized.append(m)
                else:
                    sanitized.append(
                        AIMessage(
                            content=m.content,
                            tool_calls=valid,
                            id=m.id,
                            name=m.name,
                            additional_kwargs=m.additional_kwargs,
                        )
                    )
            elif m.content:
                kw = getattr(m, 'additional_kwargs', {}) or {}
                sanitized.append(AIMessage(content=m.content, id=m.id, name=m.name, additional_kwargs=kw))
            else:
                logger.debug(
                    f"Dropping orphaned AIMessage with tool_calls: "
                    f"{[tc['id'] for tc in m.tool_calls]}"
                )
        elif isinstance(m, ToolMessage):
            if m.tool_call_id in tool_call_ids_in_ai:
                sanitized.append(m)
            else:
                logger.debug(
                    f"Dropping orphaned ToolMessage: {m.tool_call_id}"
                )
        else:
            sanitized.append(m)

    return sanitized


def _make_pre_model_hook(system_prompt: str):
    from langchain_core.messages import SystemMessage

    def hook(state):
        messages = state.get("messages", [])
        sanitized = _sanitize_messages(messages)

        llm_messages = [SystemMessage(content=system_prompt)] + sanitized

        state_messages = [RemoveMessage(id=REMOVE_ALL_MESSAGES)] + sanitized

        if sanitized != messages:
            removed_tc = len(messages) - len(sanitized)
            logger.info(
                f"[pre_model_hook] Sanitized messages: "
                f"original={len(messages)}, sanitized={len(sanitized)}, "
                f"removed_orphans={removed_tc}"
            )

        return {
            "messages": state_messages,
            "llm_input_messages": llm_messages,
        }

    return hook


def make_agent(tools, prompt, model_id=None, agent_type="chat"):
    logger.info(
        f"Creating agent: agent_type={agent_type}, tools_count={len(tools)}, model_id={model_id}"
    )
    start_time = time.time()

    llm = build_llm(model_id, agent_type)

    try:
        agent = create_react_agent(
            llm,
            tools,
            prompt=prompt,
            pre_model_hook=_make_pre_model_hook(prompt),
            checkpointer=_memory_store,
        )
    except TypeError:
        try:
            agent = create_react_agent(
                llm,
                tools,
                state_modifier=_make_pre_model_hook(prompt),
                checkpointer=_memory_store,
            )
        except TypeError:
            agent = create_react_agent(
                llm,
                tools,
                prompt=prompt,
                checkpointer=_memory_store,
            )

    elapsed = time.time() - start_time
    logger.info(
        f"Agent created successfully: elapsed={elapsed:.2f}s, agent_type={agent_type}"
    )
    return agent


async def stream_agent_response(agent, session_id: str, user_content: str):
    logger.info(
        f"[Agent Stream] Starting: session={session_id}, content_length={len(user_content)}"
    )

    config = {"configurable": {"thread_id": session_id}}
    full_response = ""
    tool_calls = 0
    stream_chunks = 0
    start_time = time.time()

    from ..tools import get_status_map
    TOOL_STATUS_MAP = get_status_map()
    TOOL_STATUS_MAP["knowledge_search"] = "正在搜索知识库..."

    async for event in agent.astream_events(
        {"messages": [HumanMessage(content=user_content)]},
        config=config,
        version="v2",
    ):
        kind = event.get("event")
        if kind == "on_chat_model_stream":
            chunk = event["data"]["chunk"]
            if hasattr(chunk, "content") and chunk.content:
                full_response += chunk.content
                stream_chunks += 1
                yield ("content", chunk.content)
        elif kind == "on_tool_start":
            tool_calls += 1
            tool_name = event.get("name", "")
            tool_input = event["data"].get("input", {})
            status_msg = TOOL_STATUS_MAP.get(tool_name, f"正在执行工具 {tool_name}...")
            logger.info(
                f"[Agent Stream] Tool #{tool_calls} starting: name={tool_name}, input={str(tool_input)[:500]}"
            )
            status_data = {"status": status_msg}
            if tool_name == "knowledge_search" and tool_input.get("query"):
                status_data["search_query"] = tool_input["query"]
            yield ("status", status_data)
        elif kind == "on_tool_end":
            tool_output = event["data"].get("output", "")
            tool_name = event.get("name", "")
            output_str = tool_output.content if hasattr(tool_output, "content") else str(tool_output)
            logger.info(
                f"[Agent Stream] Tool completed: name={tool_name}, output_length={len(output_str)}, output_preview={output_str[:300]}"
            )
            if tool_name == "knowledge_search" and output_str:
                try:
                    parsed = json.loads(output_str)
                    if parsed.get("results"):
                        yield ("search_results", parsed["results"])
                except (json.JSONDecodeError, TypeError):
                    pass

    elapsed = time.time() - start_time
    logger.info(
        f"[Agent Stream] Completed: session={session_id}, elapsed={elapsed:.2f}s, stream_chunks={stream_chunks}, tool_calls={tool_calls}, response_length={len(full_response)}"
    )
