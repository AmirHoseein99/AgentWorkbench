import subprocess
from logger import get_logger
from agent.tools.base import BaseTool


class PythonExecutorTool(BaseTool):
    name = "python_executor"
    description = "A tool for executing Python code."
    schema = {
        "type": "object",
        "properties": {
            "code": {"type": "string", "description": "The Python code to execute."},
        },
        "required": ["code"],
    }

    def execute(self, code: str) -> str:
        logger = get_logger("python_executor_tool")
        logger.info(f"Executing Python code: {code}")
        try:
            local_vars = {}
            exec(code, {}, local_vars)

            logger.info(f"Execution result: {local_vars.get('result')}")
            return local_vars.get("result")

        except subprocess.CalledProcessError as e:
            logger.exception(f"Error executing code: {e}")
            return f"Error executing code: {e}"
