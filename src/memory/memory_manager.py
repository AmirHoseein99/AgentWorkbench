import os
import json
import shutil
from typing import List, Any
from pathlib import Path
from llm.openrouter import OpenRouterAPI
from llm.prompts.memory_prompt import MEMORY_SUMMARIZER_PROMPT
from core.config import setting


def initialize_conversation(conversation_id: str) -> None:
    conversation_path = _conversation_path(conversation_id)

    conversation_path.parent.mkdir(parents=True, exist_ok=True)

    if not conversation_path.exists():
        _write_json(conversation_path, [])

    memory_path = _memory_path(conversation_id)

    if not memory_path.exists():
        _create_memory(conversation_id)


def remove_conversation(conversation_id: str) -> None:
    conversation_dir = _conversation_path(conversation_id).parent

    if conversation_dir.exists():
        shutil.rmtree(conversation_dir)


def load_conversation(conversation_id: str) -> List:

    conversation_path = _conversation_path(conversation_id)

    if not conversation_path.exists():
        return []
    try:
        data = _read_json(conversation_path)
        normalized = []

        for m in data:
            normalized.append(
                {
                    "role": m["role"],
                    "content": (
                        m["content"]
                        if isinstance(m["content"], str)
                        else json.dumps(m["content"])
                    ),
                }
            )

        return normalized

    except Exception:
        return []


def append_to_conversation(conversation_id, role, content, tool_name=None):
    conversation_path = _conversation_path(conversation_id)
    payload = load_conversation(conversation_id)

    entry = {"role": role, "content": content}

    if tool_name:
        entry["tool_name"] = tool_name

    payload.append(entry)

    _write_json(conversation_path, payload)


def _create_memory(conversation_id: str):
    memory_path = _memory_path(conversation_id)
    memory_path.parent.mkdir(parents=True, exist_ok=True)
    _write_json(
        memory_path,
        {"summary": "", "facts": [], "open_tasks": [], "last_summarized_index": 0},
    )


def load_memory(conversation_id: str):
    memory_path = _memory_path(conversation_id)
    if not memory_path.exists():
        return {
            "summary": "",
            "facts": [],
            "open_tasks": [],
            "last_summarized_index": 0,
        }
    return _read_json(_memory_path(conversation_id))


def summarize_conversation(conversation_id: str) -> None:
    llm_api = OpenRouterAPI()
    conversation = load_conversation(conversation_id=conversation_id)
    memory = load_memory(conversation_id)
    new_messages = _get_new_messages(conversation, memory["last_summarized_index"])
    messages = [
        {
            "role": "system",
            "content": MEMORY_SUMMARIZER_PROMPT,
        },
        {
            "role": "user",
            "content": f"""
                    Current memory:

                    {json.dumps(memory, indent=2)}

                    New conversation messages:

                    {json.dumps(new_messages, indent=2)}

                    Update the memory based on these new messages.
                """,
        },
    ]

    response = llm_api.call_openrouter_api(messages=messages, caller="memory_manager")
    memory = json.loads(response["choices"][0]["message"]["content"])
    memory["last_summarized_index"] = len(conversation) - 1
    _save_memory(conversation_id=conversation_id, memory=memory)


def get_context(conversation_id: str):
    conversation = load_conversation(conversation_id)

    if len(conversation) <= setting.CONVERSATION_MEMORY_THRESHOLD:
        return conversation

    memory = load_memory(conversation_id)

    if (
        len(conversation) - memory["last_summarized_index"]
        > setting.CONTEXT_WINDOW_SIZE
    ):
        summarize_conversation(conversation_id)
        memory = load_memory(conversation_id)

    return [
        {"role": "system", "content": _format_memory(memory)},
        *conversation[-setting.CONTEXT_WINDOW_SIZE :],
    ]


# private helpers
def _read_json(conversation_path: Path) -> List:
    with open(conversation_path, "r") as f:
        return json.load(f)


def _write_json(conversation_path: Path, payload: Any) -> None:

    # atomic write
    tmp_path = conversation_path.with_suffix(".tmp")

    tmp_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=4), encoding="utf-8"
    )

    os.replace(tmp_path, conversation_path)


def _conversation_path(conversation_id) -> Path:
    return Path("data") / "conversations" / str(conversation_id) / "conversation.json"


def _memory_path(conversation_id) -> Path:
    return Path("data") / "conversations" / str(conversation_id) / "memory.json"


def _save_memory(conversation_id, memory):
    _write_json(_memory_path(conversation_id), memory)


def _format_memory(memory):

    facts = "\n".join(f"- {fact}" for fact in memory["facts"])

    tasks = "\n".join(f"- {task}" for task in memory["open_tasks"])

    return f"""
Conversation Summary:
{memory["summary"]}

Important Facts:
{facts}

Open Tasks:
{tasks}
"""


def _get_new_messages(conversation, last_index):
    return conversation[last_index + 1 :]
