"""Research note generator — LangGraph version.

Same task, same tools, same output as research_note_pai.py.
Different framework. We build the agent loop explicitly as a graph.
"""

import time
from datetime import datetime
from typing import Annotated, Literal
from zoneinfo import ZoneInfo

import httpx
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field
from rich.console import Console
from rich.panel import Panel

from week3_langgraph_pydantic_ai.config import settings


console = Console()


# ============================================================
# Output schema — same as PAI version
# ============================================================


class KeyPoint(BaseModel):
    point: str = Field(description="One concrete claim, one sentence.")
    evidence: str = Field(description="Specific support — quote, fact, or example.")


class ResearchNote(BaseModel):
    """A structured research note on a topic."""

    title: str = Field(description="A specific, evocative title.")
    summary: str = Field(description="One-paragraph summary, ~60 words.")
    key_points: list[KeyPoint] = Field(
        description="Three to five key points with evidence.",
        min_length=3,
        max_length=5,
    )
    sources_mentioned: list[str] = Field(description="URLs or named sources.")
    generated_at: str = Field(description="ISO timestamp when generated.")


# ============================================================
# Graph state
# ============================================================


class GraphState(BaseModel):
    """The graph's state. `messages` accumulates the conversation
    (user, assistant, tool result messages)."""

    # The Annotated[..., add_messages] pattern tells LangGraph to APPEND
    # to this list rather than replace it. Without this, each node would
    # overwrite the messages list entirely.
    messages: Annotated[list[BaseMessage], add_messages]

    # The final structured output (filled in by the last node)
    final_note: ResearchNote | None = None


# ============================================================
# Tools — defined as LangChain @tool functions
# ============================================================

# Shared HTTP client. In production this would be properly scoped.
_http_client: httpx.Client | None = None


def _get_client() -> httpx.Client:
    global _http_client
    if _http_client is None:
        _http_client = httpx.Client()
    return _http_client


@tool
def fetch_url(url: str) -> str:
    """Fetch a web page and return the first 5000 characters.

    Use when you need current information from a specific URL the user
    has provided or that's clearly relevant to the topic.
    """
    console.print(f"[yellow]  → fetch_url({url})[/yellow]")
    try:
        response = _get_client().get(
            url,
            timeout=10.0,
            follow_redirects=True,
            headers={"User-Agent": "research-note-agent/0.1"},
        )
        response.raise_for_status()
        text = response.text[:5000]
        console.print(f"[green]  ← {len(text)} chars[/green]")
        return f"URL: {url}\nStatus: {response.status_code}\n\n{text}"
    except Exception as e:
        return f"Error fetching {url}: {type(e).__name__}: {e}"


@tool
def get_current_date(timezone: str = "UTC") -> str:
    """Get today's date in the specified IANA timezone.

    Use this to timestamp the research note or to know what 'current' means.
    """
    console.print(f"[yellow]  → get_current_date({timezone})[/yellow]")
    try:
        now = datetime.now(ZoneInfo(timezone))
        result = now.isoformat()
        console.print(f"[green]  ← {result}[/green]")
        return result
    except Exception as e:
        return f"Error: {type(e).__name__}: {e}"


TOOLS = [fetch_url, get_current_date]
TOOLS_BY_NAME = {t.name: t for t in TOOLS}


# ============================================================
# Models — one for tool use, one for final structured output
# ============================================================

# The tool-using model
MODEL = ChatAnthropic(
    model="claude-haiku-4-5-20251001",
    max_tokens=2048,
    api_key=settings.anthropic_api_key,
).bind_tools(TOOLS)

# The structured-output model (same underlying model, different mode)
STRUCTURED_MODEL = ChatAnthropic(
    model="claude-haiku-4-5-20251001",
    max_tokens=2048,
    api_key=settings.anthropic_api_key,
).with_structured_output(ResearchNote)


SYSTEM_PROMPT = (
    "You produce structured research notes on technical topics. "
    "Use the available tools when current information matters. "
    "For key points: each point must have specific evidence — a quote, a fact "
    "with a number, a named tool/product. Vague evidence is the failure mode."
)


# ============================================================
# Nodes
# ============================================================


def agent_node(state: GraphState) -> dict:
    """The 'thinking' node — calls the model with current messages, returns reply."""
    console.print("[dim]→ agent[/dim]")
    response = MODEL.invoke(state.messages)
    return {"messages": [response]}


def tool_node(state: GraphState) -> dict:
    """Execute any tool calls in the most recent AI message."""
    console.print("[dim]→ tools[/dim]")
    last_message = state.messages[-1]
    if not isinstance(last_message, AIMessage) or not last_message.tool_calls:
        return {"messages": []}

    new_messages = []
    for tool_call in last_message.tool_calls:
        tool_fn = TOOLS_BY_NAME[tool_call["name"]]
        result = tool_fn.invoke(tool_call["args"])
        new_messages.append(
            ToolMessage(
                content=str(result),
                tool_call_id=tool_call["id"],
                name=tool_call["name"],
            )
        )
    return {"messages": new_messages}


def finalize_node(state: GraphState) -> dict:
    """Once the agent has stopped calling tools, ask it to produce
    the structured ResearchNote from everything it's gathered."""
    console.print("[dim]→ finalize[/dim]")

    # Pass the entire conversation (including tool results) to the
    # structured-output model to extract the final ResearchNote
    note = STRUCTURED_MODEL.invoke(
        [
            SystemMessage(
                content=(
                    "Based on the conversation so far, produce the final structured "
                    "research note. Use information gathered from tool calls."
                )
            ),
            *state.messages,
        ]
    )
    return {"final_note": note}


# ============================================================
# Conditional edge: after the agent, do we run tools or finalize?
# ============================================================


def should_continue(state: GraphState) -> Literal["tools", "finalize"]:
    """If the last AI message has tool calls, run them. Otherwise finalize."""
    last_message = state.messages[-1]
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "tools"
    return "finalize"


# ============================================================
# Build the graph
# ============================================================


def build_graph():
    builder = StateGraph(GraphState)

    builder.add_node("agent", agent_node)
    builder.add_node("tools", tool_node)
    builder.add_node("finalize", finalize_node)

    builder.add_edge(START, "agent")
    builder.add_conditional_edges(
        "agent",
        should_continue,
        {"tools": "tools", "finalize": "finalize"},
    )
    builder.add_edge("tools", "agent")  # cycle back after tools
    builder.add_edge("finalize", END)

    return builder.compile()


# ============================================================
# Run + measure
# ============================================================


def run(topic: str) -> tuple[ResearchNote, dict]:
    """Run the graph on a topic and return (note, metrics)."""
    console.print(f"\n[bold magenta]LangGraph:[/bold magenta] {topic}\n")

    graph = build_graph()
    initial = {
        "messages": [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=topic),
        ],
        "final_note": None,
    }

    start = time.perf_counter()
    final_state = graph.invoke(initial)
    elapsed = time.perf_counter() - start

    # Extract token usage from messages
    input_tokens = 0
    output_tokens = 0
    for msg in final_state["messages"]:
        if isinstance(msg, AIMessage) and msg.usage_metadata:
            input_tokens += msg.usage_metadata.get("input_tokens", 0)
            output_tokens += msg.usage_metadata.get("output_tokens", 0)

    metrics = {
        "elapsed_sec": elapsed,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "graph_steps": len(
            [m for m in final_state["messages"] if isinstance(m, AIMessage)]
        ),
    }
    return final_state["final_note"], metrics


def display(note: ResearchNote, metrics: dict) -> None:
    console.print(
        Panel(
            f"[bold]{note.title}[/bold]\n\n"
            f"[dim]{note.summary}[/dim]\n\n"
            + "\n\n".join(
                f"[magenta]{i + 1}. {kp.point}[/magenta]\n   [dim]Evidence:[/dim] {kp.evidence}"
                for i, kp in enumerate(note.key_points)
            )
            + (
                f"\n\n[dim]Sources: {', '.join(note.sources_mentioned)}[/dim]"
                if note.sources_mentioned
                else "\n\n[dim]Sources: (general knowledge)[/dim]"
            )
            + f"\n\n[dim]Generated at: {note.generated_at}[/dim]",
            title="Research Note (LangGraph)",
            border_style="magenta",
        )
    )
    console.print(
        f"\n[dim]Metrics: {metrics['elapsed_sec']:.2f}s, "
        f"{metrics['input_tokens']} in / {metrics['output_tokens']} out, "
        f"{metrics['graph_steps']} graph steps[/dim]"
    )


def main() -> None:
    topic = (
        "What's the current state of MCP (Model Context Protocol) adoption "
        "across major AI tools in mid-2026? Be specific about which tools "
        "support it and how."
    )
    note, metrics = run(topic)
    display(note, metrics)


if __name__ == "__main__":
    main()
