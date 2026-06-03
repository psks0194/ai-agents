"""Force LLMs to return JSON matching a Pydantic schema.

Each provider does this slightly differently. We'll show the Anthropic version
(via tool use as the mechanism) and OpenAI's native structured outputs.
"""

import json
from anthropic import Anthropic
from openai import OpenAI
from pydantic import BaseModel, Field
from rich.console import Console

from week1_tri_provider_agent.config import settings


console = Console()


# ============================================================
# The schema we want the LLM to return
# ============================================================


class BookSummary(BaseModel):
    """A structured summary of a book."""

    title: str = Field(description="The book's title")
    author: str = Field(description="The author's full name")
    year: int = Field(description="Year of original publication", ge=1000, le=2100)
    genre: str = Field(
        description="Primary genre (e.g. 'fantasy', 'historical fiction')"
    )
    themes: list[str] = Field(description="Major themes, 2-4 items")
    one_line_pitch: str = Field(description="A single sentence describing the book")


# ============================================================
# Anthropic: structured output via "tool use" trick
# ============================================================


def get_book_summary_anthropic(book_name: str) -> BookSummary:
    """Use Claude to summarize a book, return as a validated Pydantic model."""
    client = Anthropic(api_key=settings.anthropic_api_key)

    # Define a "tool" that's really our schema in disguise.
    # We force Claude to call this tool to give us its answer.
    schema_tool = {
        "name": "return_book_summary",
        "description": "Return a structured summary of the requested book.",
        "input_schema": BookSummary.model_json_schema(),
    }

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        tools=[schema_tool],
        tool_choice={"type": "tool", "name": "return_book_summary"},
        messages=[{"role": "user", "content": f"Summarize the book: {book_name}"}],
    )

    # Extract the tool call (we forced it, so there's exactly one)
    tool_block = next(b for b in response.content if b.type == "tool_use")
    return BookSummary.model_validate(tool_block.input)


# ============================================================
# OpenAI: native structured outputs via response_format
# ============================================================


def get_book_summary_openai(book_name: str) -> BookSummary:
    """Use GPT to summarize a book, return as a validated Pydantic model."""
    client = OpenAI(api_key=settings.openai_api_key)

    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": f"Summarize the book: {book_name}"}],
        response_format=BookSummary,
    )

    # parse() returns the parsed Pydantic model directly
    return response.choices[0].message.parsed


# ============================================================
# Demo
# ============================================================


def main() -> None:
    book = "1984 by George Orwell"

    console.print(f"\n[bold]Asking each provider to summarize:[/bold] {book}\n")

    console.print("[bold cyan]Anthropic Claude (Haiku 4.5):[/bold cyan]")
    anth = get_book_summary_anthropic(book)
    console.print_json(json.dumps(anth.model_dump(), indent=2))

    console.print("\n[bold magenta]OpenAI GPT-4o-mini:[/bold magenta]")
    oai = get_book_summary_openai(book)
    console.print_json(json.dumps(oai.model_dump(), indent=2))


if __name__ == "__main__":
    main()
