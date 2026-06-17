"""The smallest Pydantic AI agent — no tools, just a typed agent producing typed output.

Compare line-by-line to the smallest LangGraph from Day 1 (first_graph.py).
Different design philosophies become immediately visible.
"""

from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.providers.anthropic import AnthropicProvider
from rich.console import Console

from week3_langgraph_pydantic_ai.config import settings


console = Console()


# The output schema — what we want the agent to produce
class BookRecommendation(BaseModel):
    """A structured book recommendation."""

    title: str
    author: str
    one_line_pitch: str = Field(description="A single-sentence pitch.")
    target_reader: str = Field(description="Who would love this book and why.")


# The model carries the API key via its provider (our key lives in .env →
# settings, not the environment, so we pass it explicitly).
model = AnthropicModel(
    "claude-haiku-4-5-20251001",
    provider=AnthropicProvider(api_key=settings.anthropic_api_key),
)


# Define the agent — typed inputs and outputs
recommender = Agent(
    model,
    output_type=BookRecommendation,
    instructions=(
        "You recommend books based on a topic or interest. "
        "Pick well-known books that genuinely match. Avoid generic 'classics' "
        "unless they're a precise fit."
    ),
)


def main() -> None:
    topic = "I'm a software engineer becoming interested in systems thinking"

    console.print(f"[bold]Topic:[/bold] {topic}\n")

    # Run the agent — synchronous version
    result = recommender.run_sync(topic)

    # result.output is the typed BookRecommendation
    rec = result.output
    console.print(f"[bold cyan]{rec.title}[/bold cyan] by {rec.author}")
    console.print(f"[dim]{rec.one_line_pitch}[/dim]")
    console.print(f"\n[bold]Why for you:[/bold] {rec.target_reader}")

    # Usage info — token counts (usage is a property, not a method)
    usage = result.usage
    console.print(
        f"\n[dim]Tokens: {usage.input_tokens} in / {usage.output_tokens} out[/dim]"
    )


if __name__ == "__main__":
    main()
