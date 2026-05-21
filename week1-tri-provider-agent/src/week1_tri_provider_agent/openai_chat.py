"""Multi-turn chat with GPT-4o-mini — parallel to Day 1's chat.py."""

from openai import OpenAI
from week1_tri_provider_agent.config import settings
from rich.markdown import Markdown
from rich.console import Console

console = Console()
MODEL = "gpt-4o-mini"
SYSTEM_PROMPT = (
    "You are a senior Python developer mentoring a TypeScript developer who is "
    "learning Python for the first time. Be concise, give code examples when "
    "helpful, and gently note TS-Python differences when relevant."
)


def chat() -> None:
    """Main entry point for the OpenAI chat demo."""
    client = OpenAI(api_key=settings.openai_api_key)

    messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]

    console.print(
        "[bold cyan]Chat with GPT-4o-mini.[/bold cyan] "
        "Type 'exit' to quit, 'reset' to clear history.\n"
    )

    while True:
        user_input = console.input("[bold green]you:[/bold green] ").strip()

        if user_input.lower() in ("quit", "exit", "q"):
            console.print("[dim]bye![/dim]")
            break

        if user_input.lower() == "reset":
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            console.print("[italic yellow]History cleared.[/italic yellow]")
            continue

        if not user_input:
            continue

        messages.append({"role": "user", "content": user_input})

        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
        )

        assistant_text = response.choices[0].message.content or ""
        messages.append({"role": "assistant", "content": assistant_text})

        console.print("[bold blue]gpt:[/bold blue]")
        console.print(Markdown(assistant_text))
        console.print(
            f"[dim]  ({response.usage.prompt_tokens} in / "
            f"{response.usage.completion_tokens} out tokens)[/dim]\n"
        )


def main() -> None:
    chat()


if __name__ == "__main__":
    main()
