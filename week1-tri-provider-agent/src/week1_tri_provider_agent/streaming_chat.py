"""Streaming version: see Claude's response as it's generated."""

from anthropic import Anthropic
from rich.console import Console

from week1_tri_provider_agent.config import settings


console = Console()
model = "claude-haiku-4-5-20251001"
max_tokens = 1024
system_prompt = "You are a senior Python developer mentoring a TypeScript developer who is learning Python for the first time. Be concise, give code examples when helpful, and gently note TS-Python differences when relevant."


def chat_with_claude_streaming() -> None:
    client = Anthropic(api_key=settings.anthropic_api_key)
    messages: list[dict] = []

    console.print(
        "[bold green]Welcome to Claude![/bold green]"
        "Type 'quit' to exit and 'reset' to clear conversation history."
        "-------------------------------------------------------"
    )

    while True:
        user_input = console.input("[bold blue]You: [/bold blue]")

        if user_input.lower().strip() == "quit":
            console.print("[dim]Goodbye![/dim]")
            break

        if user_input.lower().strip() == "reset":
            messages = []
            console.print("[dim]Conversation history cleared.[/dim]")
            continue

        if not user_input.strip():
            continue

        messages.append({"role": "user", "content": user_input})

        console.print("[bold green]Thinking...[/bold green]")

        full_response = ""
        with client.messages.stream(
            model=model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=messages,
        ) as stream:
            for text_chunk in stream.text_stream:
                console.print(text_chunk, end="")
                full_response += text_chunk

        # Newline after the streamed response
        console.print()

        # Get the final message (with usage stats) after streaming completes
        final = stream.get_final_message()
        console.print(
            f"[dim]  ({final.usage.input_tokens} in / "
            f"{final.usage.output_tokens} out tokens)[/dim]\n"
        )

        # Add the complete response to history
        messages.append({"role": "assistant", "content": full_response})


def main() -> None:
    chat_with_claude_streaming()


if __name__ == "__main__":
    main()
