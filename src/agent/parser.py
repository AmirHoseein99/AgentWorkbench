from ..logger import get_logger
import json
TOOL_SCHEMAS = {
    "web_search": {
        "query": str
    },
    "python_executor": {
        "code": str
    }
}
VALID_RESPONSE_TYPES = {"final", "tool"}

VALID_TOOLS = {
    "web_search",
    "python_executor"
}

def agent_format_response(response):
    parser_logger = get_logger("agent_parser")
    try:
        if "choices" not in response or len(response["choices"]) == 0:
            parser_logger.error(f"Invalid OpenRouter response: {response}")
            raise ValueError("Invalid OpenRouter response")

        try:
            content = json.loads(
                response["choices"][0]["message"]["content"]
            )
        except json.JSONDecodeError as e:
            parser_logger.error(f"Invalid JSON: {e}")
            raise
        
        parser_logger.info(
            f"Received model response: "
            f"{content.get('type')}, "
            f"{content.get('response')}"
        )

        if content.get("type") not in VALID_RESPONSE_TYPES :
            raise ValueError("Invalid response type")
        
        if content.get("type") == "tool":
            if content.get("tool") not in VALID_TOOLS:
                raise ValueError("Invalid tool requested")
            
        if content["type"] == "tool":
            if "tool" not in content:
                raise ValueError("Tool response missing tool name")

            if "args" not in content:
                raise ValueError("Tool response missing args")

            schema = TOOL_SCHEMAS[content["tool"]]

            for field, expected_type in schema.items():
                value = content["args"].get(field)

                if not isinstance(value, expected_type):
                    raise ValueError(
                        f"Invalid arg '{field}' for tool {content['tool']}"
                    )
            
        parsed_response= {
            'type' : content.get('type', None),
            'tool' : content.get('tool', None),
            'args' : content.get('args', None),
            'message' : content.get('response', None)
        }
        
        return parsed_response

    except Exception as e:
        parser_logger.exception(f"Failed to parse OpenRouter response: {e}")
        raise
