"""The smallest possible OpenAI Agents SDK agent.

Compare to:
  - Week 3 Day 1: LangGraph first_graph.py
  - Week 3 Day 3: Pydantic AI pai_first_agent.py
"""

from agents import Agent, Runner, set_default_openai_key
from pydantic import BaseModel, Field
from rich.console import Console
from week4_openai_mastra.config import settings


console = Console()


# The SDK reads the key globally, not per-agent. Our key lives in .env →
# settings (not the environment), so set it explicitly once at import.
set_default_openai_key(settings.openai_api_key)


# Output schema — what we want the agent to produce
class BookRecommendation(BaseModel):
    """A structured book recommendation."""

    title: str
    author: str
    one_line_pitch: str = Field(description="A single-sentence pitch.")
    target_reader: str = Field(description="Who would love this book and why.")


# Define the agent — instructions + output type
recommender = Agent(
    name="BookRecommender",
    instructions=(
        "You recommend books based on a topic or interest. "
        "Pick well-known books that genuinely match. Avoid generic 'classics' "
        "unless they're a precise fit."
    ),
    output_type=BookRecommendation,
)


def main() -> None:
    topic = "I'm a software engineer becoming interested in systems thinking"

    console.print(f"[bold]Topic:[/bold] {topic}\n")

    # Run the agent synchronously
    result = Runner.run_sync(recommender, topic)

    rec = result.final_output
    console.print(f"[bold cyan]{rec.title}[/bold cyan] by {rec.author}")
    console.print(f"[dim]{rec.one_line_pitch}[/dim]")
    console.print(f"\n[bold]Why for you:[/bold] {rec.target_reader}")


if __name__ == "__main__":
    main()
