import json


def build_planner_prompt(user_input, tool_definitions: list[dict]) -> str:

    tools_text = "\n\n".join(
        f"""Tool Name: {t["name"]}
        Description: {t["description"]}
        Args: {json.dumps(t["schema"], indent=2)}
        """.strip()
        for t in tool_definitions
    )

    return f"""
        You are a planning module for an agent system.

        Your job is to convert user requests into a minimal sequence of tool calls.
        ----------------------------
        STRICT RULES
        ----------------------------
        You must follow these rules:
        - You must NOT answer the user question.
        - You are only allowed to output a plan.
        - Do NOT execute tools.
        - Do NOT simulate tool results.
        - Only describe tool calls.
        - If multiple steps are required (search + calculation), you MUST include multiple steps.
        - Use ONLY the provided tools (do NOT invent tools)
        - Output ONLY valid JSON
        - Do NOT explain anything
        - Do NOT include reasoning
        - Keep plans minimal (1–5 steps max)
        - Each step must represent exactly ONE tool call
        - You are ONLY allowed to output raw JSON. No wrapper fields. No commentary. No tool field.

        Available tools:
        {tools_text}

        Output format:
        {{
          "goal": "short description of the objective",
          "steps": [
            {{
              "id": 1,
              "tool": "tool_name",
              "args": {{}}
            }}
          ]
        }}

        User request:
        {user_input}
        """
