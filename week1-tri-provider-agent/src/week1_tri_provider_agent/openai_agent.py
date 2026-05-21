"""OpenAI tool-using agent — direct port of Day 2's agent.py.

Same loop, same logic. Only the API vocabulary differs.
"""

import json

from openai import OpenAI
from rich.console import Console

from week1_tri_provider_agent.config import settings
from week1_tri_provider_agent.openai_tools import (
    TOOLS_SCHEMA_OPENAI,
    TOOL_IMPLEMENTATIONS,
)

console = Console()
MODEL = "gpt-4o-mini"
MAX_STEPS = 10

SYSTEM_PROMPT = (
    "You are a helpful assistant with access to tools. "
    "When a user's question requires computation or external information, "
    "use the appropriate tool. After receiving tool results, give a clear, "
    "concise final answer."
)


def run_tool(tool_name: str, tool_input: dict) -> str:
    """Dispatch a tool call. Returns result as a string."""
    impl = TOOL_IMPLEMENTATIONS.get(tool_name)
    if impl is None:
        return f"Error: unknown tool '{tool_name}'"
    try:
        return impl(tool_input)
    except Exception as e:
        return f"Error executing {tool_name}: {type(e).__name__}: {e}"


def run_agent(user_message: str) -> str:
    """Run the agent loop until OpenAI produces a final answer."""
    client = OpenAI(api_key=settings.openai_api_key)

    messages: list[dict] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]

    for step in range(MAX_STEPS):
        console.print(f"\n[dim]--- step {step + 1} ---[/dim]")

        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS_SCHEMA_OPENAI,
        )

        message = response.choices[0].message
        finish_reason = response.choices[0].finish_reason

        console.print(
            f"[dim]finish_reason: {finish_reason}, "
            f"tokens: {response.usage.prompt_tokens}/{response.usage.completion_tokens}[/dim]"
        )

        # Append the assistant's message to history.
        # The message object has tool_calls if it requested tools.
        messages.append(message.model_dump(exclude_none=True))

        # Did GPT finish, or does it want tool calls?
        if finish_reason == "stop":
            return message.content or ""

        if finish_reason == "tool_calls":
            # OpenAI provides tool calls under message.tool_calls
            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                # Arguments come as a JSON string — we need to parse them
                tool_input = json.loads(tool_call.function.arguments)

                console.print(
                    f"[yellow]→ tool call:[/yellow] [bold]{tool_name}[/bold]"
                    f"({tool_input})"
                )
                result = run_tool(tool_name, tool_input)
                console.print(f"[green]← result:[/green] {result}")

                # Each tool result is a separate message with role 'tool'
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result,
                    }
                )
            continue

        return f"[Agent stopped: {finish_reason}]"

    return "[Agent hit max steps without completing]"


def main() -> None:
    console.print(
        "[bold cyan]OpenAI tool-using agent.[/bold cyan] Type 'exit' to quit.\n"
    )

    while True:
        user_input = console.input("[bold green]you:[/bold green] ").strip()
        if user_input.lower() in ("exit", "quit", "q"):
            break
        if not user_input:
            continue

        final = run_agent(user_input)
        console.print(f"\n[bold blue]agent:[/bold blue] {final}\n")


if __name__ == "__main__":
    main()
