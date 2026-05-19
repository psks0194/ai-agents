"""A multi-turn conversation with Claude. You type, Claude responds, repeat."""

from anthropic import Anthropic
from rich.console import Console
from rich.markdown import Markdown

from week1_tri_provider_agent.config import settings

console = Console()
model = "claude-haiku-4-5-20251001"
max_tokens = 1024


def chat_with_claude() -> None:
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

        with console.status("[bold green]Thinking...[/bold green]"):
            message = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system="You are a senior Python developer mentoring a TypeScript developer who is learning Python for the first time. Be concise, give code examples when helpful, and gently note TS-Python differences when relevant.",
                messages=messages,
            )

        assistant_respnse = ""
        for block in message.content:
            if block.type == "text":
                assistant_respnse += block.text

        messages.append({"role": "assistant", "content": assistant_respnse})
        console.print(Markdown(assistant_respnse))

        console.print(
            f"Input tokens: {message.usage.input_tokens} | Output tokens: {message.usage.output_tokens}"
        )


def main() -> None:
    chat_with_claude()


if __name__ == "__main__":
    main()
