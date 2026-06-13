"""A 'scratchpad memory' — structured notes an agent maintains across turns.

Unlike conversation history (which is unstructured dialogue), the scratchpad
holds typed, structured facts the agent has accumulated and can reference.

Common in research agents, content pipelines, multi-step planning systems.
"""

from pydantic import BaseModel, Field
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

from week2_agent_patterns.llm import call_anthropic


console = Console()


# ============================================================
# The scratchpad data shape
# ============================================================


class ScratchpadNote(BaseModel):
    """One structured note on the scratchpad."""

    topic: str = Field(description="Short tag/category for the note.")
    content: str = Field(description="The note itself — one or two sentences.")
    added_at_step: int = Field(description="Which step in the agent's run added this.")


class Scratchpad(BaseModel):
    """The full scratchpad — agent's structured working memory."""

    notes: list[ScratchpadNote] = Field(default_factory=list)
    decisions: list[str] = Field(
        default_factory=list,
        description="Decisions the agent has committed to during this run.",
    )

    def add_note(self, topic: str, content: str, step: int) -> None:
        self.notes.append(
            ScratchpadNote(topic=topic, content=content, added_at_step=step)
        )

    def commit_decision(self, decision: str) -> None:
        self.decisions.append(decision)

    def render(self) -> str:
        """Render the scratchpad as text the LLM can read."""
        if not self.notes and not self.decisions:
            return "(scratchpad is empty)"

        parts = []
        if self.notes:
            parts.append("NOTES:")
            for n in self.notes:
                parts.append(f"  [{n.topic}] (step {n.added_at_step}): {n.content}")
        if self.decisions:
            parts.append("\nDECISIONS:")
            for d in self.decisions:
                parts.append(f"  • {d}")
        return "\n".join(parts)


# ============================================================
# A demo: research agent using a scratchpad
# ============================================================


class ResearchStep(BaseModel):
    """One step of the research agent's reasoning."""

    note_to_add: str | None = Field(
        default=None,
        description=(
            "If you learned something useful this step, add a note. "
            "Otherwise null. Be specific."
        ),
    )
    note_topic: str | None = Field(
        default=None,
        description="Short tag for the note. Required if note_to_add is set.",
    )
    decision: str | None = Field(
        default=None,
        description=(
            "If you're committing to a conclusion this step, state it. Otherwise null."
        ),
    )
    next_question: str | None = Field(
        default=None,
        description=(
            "What to research next. Null if you have enough to write the final answer."
        ),
    )
    ready_to_conclude: bool = Field(
        description="True if you have enough notes to write the final answer."
    )


RESEARCH_SYSTEM = (
    "You are a research agent maintaining a scratchpad of notes and decisions. "
    "At each step you see: the user's question, your scratchpad so far, and the "
    "most recent finding. You decide what note to add (if any), whether to "
    "commit a decision, what to research next, or whether to conclude. "
    "\n\n"
    "Be ruthless: only add notes for genuinely useful findings. "
    "Only commit decisions when you have enough evidence. "
    "Conclude as soon as the scratchpad has enough to answer."
)


WORKER_SYSTEM = (
    "Answer the question concisely with specific, concrete information. "
    "2-3 short paragraphs. Name real tools, real numbers, real names."
)


def worker(question: str) -> str:
    from week2_agent_patterns.llm import call_text_anthropic

    return call_text_anthropic(prompt=question, system=WORKER_SYSTEM, max_tokens=512)


def research_with_scratchpad(
    question: str, max_steps: int = 6
) -> tuple[str, Scratchpad]:
    """Run a research loop using a scratchpad."""
    scratchpad = Scratchpad()
    last_finding = "(no findings yet)"

    console.print(f"\n[bold]Question:[/bold] {question}\n")

    for step in range(1, max_steps + 1):
        console.print(f"\n[dim]--- Step {step}/{max_steps} ---[/dim]")
        console.print(f"[dim]Scratchpad:[/dim]\n{scratchpad.render()}\n")

        prompt = (
            f"User question: {question}\n\n"
            f"Current scratchpad:\n{scratchpad.render()}\n\n"
            f"Most recent finding:\n{last_finding}\n\n"
            f"Step {step} of {max_steps}. What's your next move?"
        )

        decision = call_anthropic(prompt, ResearchStep, system=RESEARCH_SYSTEM)

        # Apply the agent's decisions to the scratchpad
        if decision.note_to_add and decision.note_topic:
            scratchpad.add_note(
                topic=decision.note_topic,
                content=decision.note_to_add,
                step=step,
            )
            console.print(
                f"[cyan]Added note ({decision.note_topic}):[/cyan] "
                f"{decision.note_to_add}"
            )

        if decision.decision:
            scratchpad.commit_decision(decision.decision)
            console.print(f"[green]Committed decision:[/green] {decision.decision}")

        if decision.ready_to_conclude:
            console.print(f"\n[bold green]Step {step}: ready to conclude.[/bold green]")
            break

        if decision.next_question:
            console.print(f"[yellow]Researching:[/yellow] {decision.next_question}")
            last_finding = worker(decision.next_question)
            console.print(
                Panel(last_finding, title="Worker finding", border_style="magenta")
            )
    else:
        console.print(f"[yellow]Hit max_steps ({max_steps}). Concluding.[/yellow]")

    # Final write-up
    final_prompt = (
        f"User question: {question}\n\n"
        f"Your scratchpad notes:\n{scratchpad.render()}\n\n"
        "Write the final answer to the user's question, drawing on your notes."
    )
    from week2_agent_patterns.llm import call_text_anthropic

    final = call_text_anthropic(
        prompt=final_prompt,
        max_tokens=1024,
        system="Write a clear, well-organized answer based on the research notes provided.",
    )

    console.print(Panel(Markdown(final), title="Final answer", border_style="green"))
    return final, scratchpad


def main() -> None:
    question = (
        "I'm building an open-source MCP server. What are the 3-4 most important "
        "design decisions I'll have to make early, and what are the tradeoffs?"
    )
    research_with_scratchpad(question, max_steps=6)


if __name__ == "__main__":
    main()
