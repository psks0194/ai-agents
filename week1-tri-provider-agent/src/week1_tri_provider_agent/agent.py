"""A tool-using agent. The core loop that makes it an agent and not a chatbot."""

from anthropic import Anthropic
from anthropic.types import Message
from rich.console import Console

from week1_tri_provider_agent.config import settings
from week1_tri_provider_agent.tools import TOOLS_SCHEMA, TOOL_IMPLEMENTATIONS

console = Console()
MODEL = "claude-haiku-4-5-20251001"
MAX_TOKENS = 1024
MAX_STEPS = 10


SYSTEM_PROMPT = (
    "You are a helpful assistant with access to tools. "
    "When a user's question requires computation or external information, "
    "use the appropriate tool. After receiving tool results, give a clear, "
    "concise final answer."
)


def run_tool(tool_name: str, tool_input: dict) -> str:
    """Dispatch a tool call to the right implementation. Returns result as string."""
    impl = TOOL_IMPLEMENTATIONS.get(tool_name)
    if impl is None:
        return f"Error: unknown tool '{tool_name}'"
    try:
        return impl(tool_input)
    except Exception as e:
        return f"Error executing {tool_name}: {type(e).__name__}: {e}"


def agent_turn(client: Anthropic, messages: list[dict]) -> Message:
    """Make one call to Claude with the current conversation + tools available."""
    return client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=SYSTEM_PROMPT,
        tools=TOOLS_SCHEMA,
        messages=messages,
    )


def run_agent(user_message: str) -> str:
    """Run the agent loop until Claude produces a final answer."""
    client = Anthropic(api_key=settings.anthropic_api_key)

    messages: list[dict] = [{"role": "user", "content": user_message}]

    for step in range(MAX_STEPS):
        console.print(f"\n[dim]--- step {step + 1} ---[/dim]")

        # Send the conversation to Claude
        response = agent_turn(client, messages)

        console.print(
            f"[dim]stop_reason: {response.stop_reason}, "
            f"tokens: {response.usage.input_tokens}/{response.usage.output_tokens}[/dim]"
        )

        # Append Claude's response to history (always, before we do anything else)
        messages.append({"role": "assistant", "content": response.content})

        # Did Claude finish, or does it want a tool call?
        if response.stop_reason == "end_turn":
            # Extract the final text from the response
            final_text = ""
            for block in response.content:
                if block.type == "text":
                    final_text += block.text
            return final_text

        if response.stop_reason == "tool_use":
            # Find all tool_use blocks (Claude can request multiple in one turn)
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    console.print(
                        f"[yellow]→ tool call:[/yellow] [bold]{block.name}[/bold]"
                        f"({block.input})"
                    )
                    result = run_tool(block.name, block.input)
                    console.print(f"[green]← result:[/green] {result}")
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result,
                        }
                    )

            # Send all tool results back in one message
            messages.append({"role": "user", "content": tool_results})
            continue  # Go back to the top of the loop, send to Claude again

        # Some other stop_reason (max_tokens, stop_sequence) — bail
        return f"[Agent stopped: {response.stop_reason}]"

    return "[Agent hit max steps without completing]"


def main() -> None:
    """Interactive agent CLI."""
    console.print(
        "[bold cyan]Tool-using agent ready.[/bold cyan] Type 'exit' to quit.\n"
    )

    while True:
        user_input = console.input("[bold green]you:[/bold green] ").strip()
        if user_input.lower() in ("exit", "quit"):
            break
        if not user_input:
            continue

        final = run_agent(user_input)
        console.print(f"\n[bold blue]agent:[/bold blue] {final}\n")


if __name__ == "__main__":
    main()
