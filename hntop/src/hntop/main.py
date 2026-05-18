"""Hacker News Top — fetch and display top HN stories."""

import argparse
import asyncio
from rich.console import Console
from rich.table import Table

from hntop.client import fetch_top_stories
from hntop.config import AppSettings
from hntop.models import Story

console = Console()


def parse_arguments(settings: AppSettings) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="HN Top — fetch and display top HN stories."
    )
    parser.add_argument(
        "--count",
        type=int,
        default=settings.default_count,
        help="Number of stories to fetch",
    )
    parser.add_argument(
        "--min-score",
        type=int,
        default=settings.default_min_score,
        help="Minimum score for stories",
    )
    args = parser.parse_args()
    return args


def render_stories(stories: list[Story], min_score: int) -> None:
    """Render the stories in a table."""

    filtered_stories = [s for s in stories if s.score >= min_score]

    if not filtered_stories:
        console.print(
            f"[yellow]No stories met the filter (min score: {min_score}).[/yellow]"
        )
        return

    table = Table(
        title=f"Hacker News — Top {len(filtered_stories)}"
        + (f" (score ≥ {min_score})" if min_score > 0 else ""),
        show_lines=False,
    )
    table.add_column("rank", style="dim", width=5)
    table.add_column("title", style="cyan", min_width=30)
    table.add_column("score", style="green")
    table.add_column("author", style="blue")
    table.add_column("comments", style="yellow")

    for i, story in enumerate(filtered_stories, 1):
        table.add_row(
            str(i),
            story.title,
            str(story.score),
            story.author,
            str(story.comments),
        )
    console.print(table)


async def run() -> None:
    """Run the HN Top app."""
    settings = AppSettings()
    args = parse_arguments(settings)

    with console.status(f"[bold green]Fetching top {args.count} stories..."):
        stories = await fetch_top_stories(count=args.count)

    render_stories(stories, min_score=args.min_score)


def main() -> None:
    """Entry point."""
    asyncio.run(run())


if __name__ == "__main__":
    main()
