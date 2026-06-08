"""Orchestrator-workers pattern: planning LLM dispatches tasks adaptively.

Unlike yesterday's decomposer (one-shot planning), the orchestrator runs in
a loop. At each step it sees what's been done and decides what to do next.

The loop has hard stopping conditions to prevent runaway cost.
"""

from typing import Literal

from pydantic import BaseModel, Field
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

from week2_agent_patterns.llm import call_anthropic, call_text_anthropic


console = Console()


# Loop safety — non-negotiable
MAX_ITERATIONS = 5


# ============================================================
# What the orchestrator can decide to do
# ============================================================


class OrchestratorDecision(BaseModel):
    """One decision from the orchestrator at each loop iteration."""

    action: Literal["dispatch_worker", "finalize"] = Field(
        description=(
            "'dispatch_worker' to send a research question to a worker. "
            "'finalize' if you have enough information to write the final answer."
        )
    )
    reasoning: str = Field(
        description=(
            "Brief explanation of why this action. For dispatch_worker, why this "
            "specific question is needed. For finalize, what coverage you now have."
        )
    )
    worker_task: str | None = Field(
        default=None,
        description=(
            "If action is 'dispatch_worker', the specific question to send to "
            "the worker. Be precise — workers answer literally what you ask. "
            "If action is 'finalize', leave this null."
        ),
    )


# ============================================================
# Orchestrator prompts
# ============================================================

ORCHESTRATOR_SYSTEM = (
    "You are a research orchestrator. Your job is to gather enough information "
    "to answer the user's question well, by dispatching focused sub-questions to "
    "research workers. \n\n"
    "At each step you'll see: the user's original question, your previous "
    "decisions, and any worker findings so far. You decide:\n"
    " - dispatch_worker — send a specific sub-question to a worker\n"
    " - finalize — you have enough; write the final answer\n\n"
    "Principles:\n"
    " - Don't ask sub-questions you already have answers to\n"
    " - Look at what previous findings revealed, and follow up if relevant\n"
    " - Finalize early if you have enough — extra workers cost money\n"
    f" - You have at most {MAX_ITERATIONS} iterations total"
)


def orchestrator_decide(
    original_question: str,
    history: list[dict],
    iteration: int,
) -> OrchestratorDecision:
    """The orchestrator looks at history and decides what to do next."""
    history_text = (
        "\n\n".join(
            f"Iteration {h['iter']}: dispatched worker on '{h['task']}'\n"
            f"Worker found:\n{h['finding']}"
            for h in history
        )
        if history
        else "(no workers dispatched yet)"
    )

    prompt = (
        f"Original question: {original_question}\n\n"
        f"History so far:\n{history_text}\n\n"
        f"Current iteration: {iteration} of {MAX_ITERATIONS}\n\n"
        "Decide your next action."
    )

    return call_anthropic(
        prompt=prompt,
        schema=OrchestratorDecision,
        system=ORCHESTRATOR_SYSTEM,
    )


# ============================================================
# Workers (single-task research)
# ============================================================

WORKER_SYSTEM = (
    "Answer the specific question precisely. Be concrete: name real tools, "
    "specific tradeoffs, real numbers if relevant. Avoid hedging. "
    "If you don't know something with confidence, say so explicitly. "
    "2-3 short paragraphs."
)


def worker(task: str) -> str:
    """One worker — answers a single focused question."""
    return call_text_anthropic(prompt=task, system=WORKER_SYSTEM, max_tokens=1024)


# ============================================================
# Finalizer
# ============================================================

FINALIZER_SYSTEM = (
    "You synthesize research findings into a final answer to the user's question. "
    "Weave findings together — don't just concatenate. Lead with the most "
    "actionable insight. If the question asks for a recommendation, give one "
    "(while making clear it's a recommendation, not a fact). ~400 words."
)


def finalize(original_question: str, history: list[dict]) -> str:
    """Write the final answer using all worker findings."""
    findings_text = "\n\n".join(
        f"Question: {h['task']}\nFinding:\n{h['finding']}" for h in history
    )

    prompt = (
        f"Original user question: {original_question}\n\n"
        f"Research findings:\n\n{findings_text}\n\n"
        "Write the final answer to the user's original question."
    )

    return call_text_anthropic(
        prompt=prompt,
        system=FINALIZER_SYSTEM,
        max_tokens=2048,
    )


# ============================================================
# The orchestration loop
# ============================================================


def run_orchestrator(question: str) -> str:
    """Run the orchestrator loop until finalize or MAX_ITERATIONS."""
    console.print(f"\n[bold]Question:[/bold] {question}\n")

    history: list[dict] = []

    for iteration in range(1, MAX_ITERATIONS + 1):
        console.print(f"\n[dim]--- Iteration {iteration}/{MAX_ITERATIONS} ---[/dim]")

        decision = orchestrator_decide(question, history, iteration)

        if decision.action == "finalize":
            console.print(
                Panel(
                    f"[bold]Decision:[/bold] FINALIZE\n[dim]Why:[/dim] {decision.reasoning}",
                    title="Orchestrator decision",
                    border_style="green",
                )
            )
            break

        # action == "dispatch_worker"
        if decision.worker_task is None:
            console.print(
                "[red]Orchestrator chose dispatch_worker but gave no task. Bailing.[/red]"
            )
            break

        console.print(
            Panel(
                f"[bold]Decision:[/bold] DISPATCH WORKER\n"
                f"[dim]Why:[/dim] {decision.reasoning}\n\n"
                f"[bold]Task:[/bold] {decision.worker_task}",
                title="Orchestrator decision",
                border_style="cyan",
            )
        )

        finding = worker(decision.worker_task)
        console.print(
            Panel(
                finding,
                title=f"Worker finding (iter {iteration})",
                border_style="magenta",
            )
        )

        history.append(
            {
                "iter": iteration,
                "task": decision.worker_task,
                "finding": finding,
            }
        )
    else:
        # for/else: the else runs if the loop completed without break
        # (i.e., we hit MAX_ITERATIONS without orchestrator choosing finalize)
        console.print(
            f"\n[yellow]Hit MAX_ITERATIONS ({MAX_ITERATIONS}) — forcing finalize.[/yellow]"
        )

    console.print("\n[dim]Writing final answer...[/dim]")
    final = finalize(question, history)
    console.print(
        Panel(
            Markdown(final),
            title=f"Final answer (after {len(history)} workers)",
            border_style="green",
        )
    )
    return final


def main() -> None:
    question = (
        "I'm evaluating Pydantic AI vs LangGraph for a new project. "
        "My team is TypeScript-heavy, the project is a customer support agent "
        "that needs to call 5-6 internal APIs and remember context across "
        "conversations. Help me decide."
    )
    run_orchestrator(question)


if __name__ == "__main__":
    main()
