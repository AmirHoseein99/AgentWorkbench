# ai.py
import sys
from rich import print

from llm.openrouter import OpenRouterAPI
from llm.utils import stream_to_terminal
from agent.agent import agent
from logger import get_logger
from llm.prompts.agent_system_prompt import build_agent_system_prompt


def main():
    logger = get_logger("cli")
    messages = [
        {
            "role": "system",
            "content": build_agent_system_prompt(agent.tool_definitions),
        },
    ]

    openrouter_api = OpenRouterAPI()

    print("\n[cyan]AI Assistant ready — /exit to quit, /clear to reset[/cyan]\n")

    while True:
        print("\n[bold red]You:[/bold red]")
        user_message = input("      ")

        if user_message.strip().lower() == "/exit":
            print("\n[yellow]Exiting...[/yellow]")
            logger.info("Exiting the AI Assistant.")
            sys.exit(0)

        if user_message.strip().lower() == "/clear":
            messages = [
                {
                    "role": "system",
                    "content": build_agent_system_prompt(agent.tool_definitions),
                }
            ]
            print("\n[yellow]Conversation cleared.[/yellow]\n")
            logger.info("Conversation cleared.")
            continue

        logger.info(f"User input: {user_message}")
        messages.append({"role": "user", "content": user_message})

        try:
            print("\n[blue]⠋ Thinking...[/blue]\n")

            print("[bold green]Assistant:[/bold green]\n")
            print("─" * 50)

            assisstat_response = stream_to_terminal(
                openrouter_api=openrouter_api, messages=messages
            )
            logger.info(f"Assistant response: {assisstat_response}")
            messages.append({"role": "assistant", "content": assisstat_response})
            print("\n" + "─" * 50 + "\n")

        except Exception as e:
            logger.exception(f"Error during AI response: {e}")
            print(f"\n[red]Error:[/red] {e}\n")


if __name__ == "__main__":
    main()
