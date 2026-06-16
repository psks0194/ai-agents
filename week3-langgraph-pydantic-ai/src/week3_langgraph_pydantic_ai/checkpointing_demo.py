"""Demo: checkpointing lets you stream intermediate state and resume.

LangGraph's killer feature for production. With a checkpointer:
  - Every node's output is saved
  - You can stream state as it changes
  - You can resume from any saved checkpoint
"""

from rich.console import Console

from week3_langgraph_pydantic_ai.content_loop import build_graph


console = Console()


def main() -> None:
    # Build with checkpointer enabled
    graph = build_graph(use_checkpointer=True)

    # Every run needs a thread_id — like a session identifier.
    # State persists per thread, so you can have multiple parallel
    # conversations/runs and they don't bleed into each other.
    config = {"configurable": {"thread_id": "demo-session-1"}}

    initial = {
        "topic": "the gap between using agent frameworks and building the patterns inside them",
        "max_iterations": 3,
    }

    console.print("[bold]Streaming graph execution...[/bold]\n")

    # .stream() yields state updates after each node runs
    for update in graph.stream(initial, config=config):
        # update is a dict: {node_name: partial_state}
        for node_name, partial in update.items():
            console.print(
                f"[cyan]✓ {node_name}[/cyan] updated keys: {list(partial.keys())}"
            )

    # Now retrieve the final state from the checkpointer
    console.print("\n[bold]Retrieving final state from checkpointer...[/bold]")
    final = graph.get_state(config)
    console.print(f"Final iteration: {final.values['iteration']}")
    console.print(f"Final verdict: {final.values['verdict']}")
    console.print(f"Word count: {final.values['word_count']}")
    console.print("\n[bold]Post (first 300 chars):[/bold]")
    console.print(final.values["post"][:300] + "...")


if __name__ == "__main__":
    main()
