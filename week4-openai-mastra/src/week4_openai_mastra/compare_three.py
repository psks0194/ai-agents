"""Run the same research-note task across Pydantic AI, LangGraph, and OpenAI Agents SDK.

Extends Week 3 Day 4's two-way comparison to three frameworks.
Produces the table that's the foundation for Friday's four-framework matrix.
"""

import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table


# Make Week 3's module importable. This is a small hack — in a real
# monorepo you'd structure this differently, but for the curriculum
# the path mod keeps the comparison runner self-contained.
WEEK3_SRC = Path(__file__).resolve().parents[3] / "week3-langgraph-pydantic-ai" / "src"
sys.path.insert(0, str(WEEK3_SRC))


from week3_langgraph_pydantic_ai import research_note_pai, research_note_lg  # noqa: E402
from week4_openai_mastra import research_note_oai  # noqa: E402


console = Console()


def main() -> None:
    topic = (
        "What's the current state of MCP (Model Context Protocol) adoption "
        "across major AI tools in mid-2026? Be specific about which tools "
        "support it and how."
    )

    console.print(f"[bold]Topic:[/bold] {topic}\n")
    console.print("=" * 70 + "\n")

    # Pydantic AI
    pai_note, pai_metrics = research_note_pai.run(topic)
    research_note_pai.display(pai_note, pai_metrics)
    console.print("\n" + "=" * 70 + "\n")

    # LangGraph
    lg_note, lg_metrics = research_note_lg.run(topic)
    research_note_lg.display(lg_note, lg_metrics)
    console.print("\n" + "=" * 70 + "\n")

    # OpenAI Agents SDK
    oai_note, oai_metrics = research_note_oai.run(topic)
    research_note_oai.display(oai_note, oai_metrics)

    # Three-way comparison
    console.print("\n" + "=" * 70 + "\n")
    table = Table(title="Three-framework head-to-head — same task")
    table.add_column("Metric", style="bold")
    table.add_column("Pydantic AI", style="cyan", justify="right")
    table.add_column("LangGraph", style="magenta", justify="right")
    table.add_column("OpenAI Agents SDK", style="green", justify="right")

    table.add_row(
        "Wall time",
        f"{pai_metrics['elapsed_sec']:.2f}s",
        f"{lg_metrics['elapsed_sec']:.2f}s",
        f"{oai_metrics['elapsed_sec']:.2f}s",
    )
    table.add_row(
        "Input tokens",
        f"{pai_metrics['input_tokens']:,}",
        f"{lg_metrics['input_tokens']:,}",
        f"{oai_metrics['input_tokens']:,}",
    )
    table.add_row(
        "Output tokens",
        f"{pai_metrics['output_tokens']:,}",
        f"{lg_metrics['output_tokens']:,}",
        f"{oai_metrics['output_tokens']:,}",
    )

    # Cost — different pricing per provider!
    # Anthropic Haiku 4.5: $1/M in, $5/M out
    # OpenAI GPT-5.4-mini: roughly $0.25/M in, $2/M out (verify when running)
    pai_cost = (
        pai_metrics["input_tokens"] / 1e6 * 1.00
        + pai_metrics["output_tokens"] / 1e6 * 5.00
    )
    lg_cost = (
        lg_metrics["input_tokens"] / 1e6 * 1.00
        + lg_metrics["output_tokens"] / 1e6 * 5.00
    )
    oai_cost = (
        oai_metrics["input_tokens"] / 1e6 * 0.25
        + oai_metrics["output_tokens"] / 1e6 * 2.00
    )

    table.add_row(
        "Cost (¢)",
        f"{pai_cost * 100:.3f}",
        f"{lg_cost * 100:.3f}",
        f"{oai_cost * 100:.3f}",
    )

    console.print(table)

    # Lines of code
    console.print("\n[bold]Lines of code (agent file only):[/bold]")
    pai_lines = sum(1 for _ in open(research_note_pai.__file__))
    lg_lines = sum(1 for _ in open(research_note_lg.__file__))
    oai_lines = sum(1 for _ in open(research_note_oai.__file__))
    console.print(f"  Pydantic AI:        {pai_lines} lines")
    console.print(f"  LangGraph:          {lg_lines} lines")
    console.print(f"  OpenAI Agents SDK:  {oai_lines} lines")


if __name__ == "__main__":
    main()
