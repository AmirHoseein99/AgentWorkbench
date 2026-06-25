from math import log
from os import strerror

from ..llm.prompt import SYSTEM_PROMPT
from ..llm.openrouter import OpenRouterAPI
from .parser import agent_format_response
from .tools.web_search import web_search_tool
from .tools.python_executor import python_executor_tool
from ..logger import get_logger
from ..memory.json_memory import append_to_conversation
import json

tool_calling = {"web_search": web_search_tool, "python_executor": python_executor_tool}

max_steps = 10


def call_agent(user_input, conversation_history, conversation_id: str):
    logger = get_logger("agent")

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(conversation_history)
    messages.append({"role": "user", "content": user_input})

    llm_api = OpenRouterAPI()

    for i in range(max_steps):
        logger.info(f"Step {i + 1}/{max_steps}: Sending messages to OpenRouter API.")
        logger.info("Calling OpenRouter API...")

        llm_response = llm_api.call_openrouter_api(messages=messages)
        logger.info(f'llm response in agent, {llm_response}')
        try:
            parsed_response = agent_format_response(llm_response)
        except Exception as e: 
            logger.exception(e)
            messages.append({
                "role": "assistant",
                "content": str(e)
            })
            continue

        logger.info(f"Parsed llm response: {parsed_response}")

        # --------------------
        # FINAL RESPONSE
        # --------------------
        if parsed_response.get("type") == "final":
            logger.info(f'Agent Final Response : {parsed_response}')
            append_to_conversation(
                role="assistant",
                content=parsed_response,
                conversation_id=conversation_id
            )
            return parsed_response["message"]

        # --------------------
        # TOOL CALL
        # --------------------
        if parsed_response.get("type") == "tool_call":
            tool_name = parsed_response.get("tool")
            tool_args = parsed_response.get("args")

            tool = tool_calling.get(tool_name)

            if tool is None:
                logger.error(f"Tool not found: {tool_name}")
                continue
            try:
                if not isinstance(tool_args, dict):
                    raise ValueError(f"tool_args must be dict, got {type(tool_args)}")
                
                tool_result = tool(**tool_args)
            except Exception as e:
                tool_result = str(e)
                
            append_to_conversation(
                role="assistant",
                content=parsed_response,
                conversation_id=conversation_id
            )
            messages.append({
                "role": "assistant",
                "content": json.dumps(parsed_response)
            })

            messages.append({
                "role": "assistant",
                "content": json.dumps({
                    "tool": tool_name,
                    "result": json.dumps(tool_result)
                })
            })

            append_to_conversation(
                role='tool',
                content=tool_result,
                conversation_id=conversation_id,
                tool_name=tool_name
            )

    return "Sorry, I couldn't complete the task within the step limit."