"""Streaming version of the Anthropic tool-using agent.

Same loop as agent.py, but text is printed token-by-token as it's generated.
This is what production agent UIs do.
"""

from anthropic import Anthropic
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
    """Dispatch a tool call to its implementation."""
    impl = TOOL_IMPLEMENTATIONS.get(tool_name)
    if impl is None:
        return f"Error: unknown tool '{tool_name}'"
    try:
        return impl(tool_input)
    except Exception as e:
        return f"Error executing {tool_name}: {type(e).__name__}: {e}"


def run_agent_streaming(user_message: str) -> None:
    """Run the agent loop with token-by-token streaming."""
    client = Anthropic(api_key=settings.anthropic_api_key)

    messages: list[dict] = [{"role": "user", "content": user_message}]

    for step in range(MAX_STEPS):
        console.print(f"\n[dim]--- step {step + 1} ---[/dim]")

        # Use the streaming API
        with client.messages.stream(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=SYSTEM_PROMPT,
            tools=TOOLS_SCHEMA,
            messages=messages,
        ) as stream:
            # Print text as it streams
            for text_chunk in stream.text_stream:
                console.print(text_chunk, end="")

            # When the stream ends, get the final assembled message
            response = stream.get_final_message()

        console.print()  # newline after the streamed text
        console.print(
            f"[dim]stop_reason: {response.stop_reason}, "
            f"tokens: {response.usage.input_tokens}/{response.usage.output_tokens}[/dim]"
        )

        # Append assistant's full response to history
        messages.append({"role": "assistant", "content": response.content})

        # Same loop logic as the non-streaming agent
        if response.stop_reason == "end_turn":
            return

        if response.stop_reason == "tool_use":
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
            messages.append({"role": "user", "content": tool_results})
            continue

        console.print(f"[red][Agent stopped: {response.stop_reason}][/red]")
        return

    console.print("[red][Agent hit max steps][/red]")


def main() -> None:
    console.print(
        "[bold cyan]Streaming tool-using agent.[/bold cyan] Type 'exit' to quit.\n"
    )

    while True:
        user_input = console.input("[bold green]you:[/bold green] ").strip()
        if user_input.lower() in ("exit", "quit"):
            break
        if not user_input:
            continue

        console.print()
        run_agent_streaming(user_input)
        console.print()


if __name__ == "__main__":
    main()
