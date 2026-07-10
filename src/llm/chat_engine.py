from agent.agent import agent

from llm.openrouter import OpenRouterAPI
from llm.prompts.agent_system_prompt import build_agent_system_prompt
from llm.parser import format_response, parse_openrouter_stream

openrouter_api = OpenRouterAPI()
messages = [
    {"role": "system", "content": build_agent_system_prompt(agent.tool_definitions)},
]


def ask_llm(user_input: str):
    messages.append({"role": "user", "content": user_input})
    llm_reponse = openrouter_api.call_openrouter_api(messages=messages)
    llm_reponse_content = format_response(llm_reponse)
    return llm_reponse_content


def stream_llm(user_input: str):
    messages.append({"role": "user", "content": user_input})
    for llm_response_chunk in openrouter_api.stream_openrouter_response(
        messages=messages
    ):
        parsed_llm_response = parse_openrouter_stream(llm_response_chunk)
        if parsed_llm_response:
            yield f"data: {parsed_llm_response}\n\n"

    yield "event: done\ndata: [DONE]\n\n"
