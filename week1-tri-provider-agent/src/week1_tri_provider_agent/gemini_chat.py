"""Multi-turn chat with Gemini — parallel to chat.py and openai_chat.py."""

from google import genai
from google.genai import types
from rich.console import Console
from rich.markdown import Markdown

from week1_tri_provider_agent.config import settings


console = Console()
MODEL = "gemini-2.5-flash"
SYSTEM_PROMPT = (
    "You are a senior Python developer mentoring a TypeScript developer who is "
    "learning Python for the first time. Be concise, give code examples when "
    "helpful, and gently note TS-Python differences when relevant."
)


def chat() -> None:
    client = genai.Client(api_key=settings.google_api_key)

    # Gemini uses a `chat` session abstraction — different mental model from
    # Anthropic and OpenAI, where YOU manage the message history.
    chat_session = client.chats.create(
        model=MODEL,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
        ),
    )

    console.print(
        "[bold cyan]Chat with Gemini.[/bold cyan] "
        "Type 'exit' to quit, 'reset' to clear history.\n"
    )

    while True:
        user_input = console.input("[bold green]you:[/bold green] ").strip()

        if user_input.lower() in ("exit", "quit"):
            console.print("[dim]bye![/dim]")
            break

        if user_input.lower() == "reset":
            # Recreate the chat session with the same config
            chat_session = client.chats.create(
                model=MODEL,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                ),
            )
            console.print("[yellow]history cleared.[/yellow]\n")
            continue

        if not user_input:
            continue

        response = chat_session.send_message(user_input)

        assistant_text = response.text
        console.print("[bold blue]gemini:[/bold blue]")
        console.print(Markdown(assistant_text))

        usage = response.usage_metadata
        console.print(
            f"[dim]  ({usage.prompt_token_count} in / "
            f"{usage.candidates_token_count} out tokens)[/dim]\n"
        )


def main() -> None:
    chat()


if __name__ == "__main__":
    main()
