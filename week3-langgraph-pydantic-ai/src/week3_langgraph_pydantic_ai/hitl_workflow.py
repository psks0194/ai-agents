"""Human-in-the-loop content workflow.

After the critic verdict, the graph PAUSES and waits for human approval.
The human can approve (ship), reject (loop back with notes), or override
the LLM verdict entirely.

This is the LangGraph feature you can't easily build by hand.
"""

from typing import Literal

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt, Command
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from week3_langgraph_pydantic_ai.content_loop import (
    ContentState,
    scout_node,
    outline_node,
    drafter_node,
    critic_node,
)


console = Console()


# ContentState plus a slot for the human's decision.
# Defined up here so the node/routing functions below can annotate against it —
# LangGraph coerces state into whatever type a function's first arg is annotated as.
class HitlState(ContentState):
    """ContentState plus a slot for the human's decision."""

    human_decision: dict | None = None


# ============================================================
# Human approval node — uses interrupt()
# ============================================================


def human_approval_node(state: HitlState) -> dict:
    """Pause and ask the human to approve, reject, or override."""
    # Render what we're asking the human to approve
    console.print("\n" + "=" * 60)
    console.print("[bold yellow]HUMAN APPROVAL REQUIRED[/bold yellow]")
    console.print("=" * 60 + "\n")

    console.print(
        Panel(
            Markdown(state.post),
            title=f"Draft (iteration {state.iteration}) — {state.word_count} words",
            border_style="green",
        )
    )

    verdict_color = "green" if state.verdict == "ship" else "yellow"
    console.print(
        Panel(
            f"[bold]LLM verdict:[/bold] [{verdict_color}]{state.verdict.upper()}[/{verdict_color}]\n\n"
            + "\n".join(f"• {r}" for r in state.critique_reasons),
            title="Critic feedback",
            border_style=verdict_color,
        )
    )

    # interrupt() pauses the graph and surfaces a payload to the caller.
    # When the caller resumes with Command(resume=value), execution
    # continues here and `decision` is set to that value.
    decision = interrupt(
        {
            "question": "Approve this draft, request revision, or override?",
            "draft": state.post,
            "llm_verdict": state.verdict,
            "iteration": state.iteration,
        }
    )

    # decision is whatever the resuming caller passed in
    return {"human_decision": decision}


def route_after_human(state: HitlState) -> Literal["drafter", "__end__"]:
    """Decide what to do based on the human's response."""
    decision = state.human_decision

    if decision["action"] == "approve":
        console.print("\n[bold green]✓ APPROVED by human[/bold green]")
        return END

    if decision["action"] == "reject":
        notes = decision.get("notes", "(no specific notes)")
        console.print(
            f"\n[bold red]✗ REJECTED — looping back with notes: {notes}[/bold red]"
        )
        return "drafter"

    # Fallback: any other action ends the graph
    return END


# ============================================================
# Build the HITL graph
# ============================================================


def build_hitl_graph():
    builder = StateGraph(HitlState)

    builder.add_node("scout", scout_node)
    builder.add_node("outline", outline_node)
    builder.add_node("drafter", drafter_node)
    builder.add_node("critic", critic_node)
    builder.add_node("human_approval", human_approval_node)

    builder.add_edge(START, "scout")
    builder.add_edge("scout", "outline")
    builder.add_edge("outline", "drafter")
    builder.add_edge("drafter", "critic")
    builder.add_edge("critic", "human_approval")

    builder.add_conditional_edges(
        "human_approval",
        route_after_human,
        {"drafter": "drafter", END: END},
    )

    # MemorySaver is essential — interrupts require a checkpointer
    return builder.compile(checkpointer=MemorySaver())


# ============================================================
# Run it
# ============================================================


def main() -> None:
    graph = build_hitl_graph()
    config = {"configurable": {"thread_id": "hitl-demo"}}

    initial = {
        "topic": "why agent frameworks are wrappers around the 80-line agent loop",
        "max_iterations": 3,
    }

    console.print("[bold]Starting HITL graph...[/bold]\n")

    # First run — will execute until it hits the interrupt
    for chunk in graph.stream(initial, config=config):
        for node_name in chunk:
            if node_name != "__interrupt__":
                console.print(f"[dim cyan]✓ {node_name} completed[/dim cyan]")

    # When the graph hits interrupt(), execution pauses.
    # We get control back here. The state is saved via the checkpointer.

    # Get the current state to confirm we're at the interrupt point
    snapshot = graph.get_state(config)
    console.print(f"\n[dim]Graph paused. Next node: {snapshot.next}[/dim]")

    # Loop until the graph is fully done
    while snapshot.next:
        # Ask the human (us) for input
        console.print("\n[bold cyan]Your decision:[/bold cyan]")
        console.print("  1. approve — ship the post")
        console.print("  2. reject — send back to drafter with notes")
        choice = console.input("[bold]Choice (1/2):[/bold] ").strip()

        if choice == "1":
            decision = {"action": "approve"}
        elif choice == "2":
            notes = console.input("[bold]Notes for the drafter:[/bold] ").strip()
            decision = {"action": "reject", "notes": notes}
        else:
            console.print("[red]Invalid. Treating as approve.[/red]")
            decision = {"action": "approve"}

        # Resume the graph with the human's decision
        console.print("\n[dim]Resuming graph...[/dim]\n")
        for chunk in graph.stream(Command(resume=decision), config=config):
            for node_name in chunk:
                if node_name != "__interrupt__":
                    console.print(f"[dim cyan]✓ {node_name} completed[/dim cyan]")

        snapshot = graph.get_state(config)
        if snapshot.next:
            console.print(f"\n[dim]Paused again. Next: {snapshot.next}[/dim]")

    # Graph is done
    final = graph.get_state(config)
    console.print("\n[bold green]Graph complete.[/bold green]")
    console.print(f"Total iterations: {final.values.get('iteration', 0)}")


if __name__ == "__main__":
    main()
