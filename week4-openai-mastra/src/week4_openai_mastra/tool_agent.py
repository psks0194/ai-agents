"""OpenAI Agents SDK tool-using agent.

Third implementation of the canonical tool-use loop. Compare:
  - Week 1 Day 2: raw Anthropic SDK (~80 lines, you write the loop)
  - Week 3 Day 3: Pydantic AI (@agent.tool decorator, loop hidden)
  - Week 4 Day 1: OpenAI Agents SDK (@function_tool decorator, Runner manages loop)
"""

from datetime import datetime
from zoneinfo import ZoneInfo

import httpx
from agents import Agent, Runner, function_tool, set_default_openai_key
from rich.console import Console
from week4_openai_mastra.config import settings


console = Console()

set_default_openai_key(settings.openai_api_key)


# Shared HTTP client for tool calls
_http_client = httpx.Client()


# ============================================================
# Tools — defined as decorated Python functions
# ============================================================


@function_tool
def calculator(expression: str) -> str:
    """Evaluate a basic mathematical expression.

    Supports +, -, *, /, **, and parentheses. Use this whenever you need
    to compute a numeric result.

    Args:
        expression: A math expression like '47 * 83 + 199' or '(5 + 3) ** 2'.
    """
    console.print(f"[yellow]  → calculator({expression!r})[/yellow]")
    try:
        result = eval(expression, {"__builtins__": {}}, {})
        console.print(f"[green]  ← {result}[/green]")
        return str(result)
    except Exception as e:
        return f"Error: {type(e).__name__}: {e}"


@function_tool
def get_current_time(timezone: str) -> str:
    """Get the current date and time in a specified IANA timezone.

    Use this when the user asks about the current time, today's date, or
    anything time-sensitive. Returns ISO format with timezone.

    Args:
        timezone: IANA timezone name, e.g. 'Asia/Kolkata', 'America/New_York',
            'Europe/London', 'UTC'. Default 'UTC' if user gave no preference.
    """
    console.print(f"[yellow]  → get_current_time({timezone!r})[/yellow]")
    try:
        now = datetime.now(ZoneInfo(timezone))
        result = now.isoformat()
        console.print(f"[green]  ← {result}[/green]")
        return result
    except Exception as e:
        return f"Error: {type(e).__name__}: {e}"


@function_tool
def fetch_url(url: str) -> str:
    """Fetch the contents of a web page.

    Returns the first 5000 characters of the page text. Use when you need
    current information from a specific URL.

    Args:
        url: The full URL to fetch, including https://.
    """
    console.print(f"[yellow]  → fetch_url({url!r})[/yellow]")
    try:
        response = _http_client.get(
            url,
            timeout=10.0,
            follow_redirects=True,
            headers={"User-Agent": "week4-agent/0.1"},
        )
        response.raise_for_status()
        text = response.text[:5000]
        console.print(f"[green]  ← {len(text)} chars[/green]")
        return f"URL: {url}\nStatus: {response.status_code}\n\n{text}"
    except Exception as e:
        return f"Error fetching {url}: {type(e).__name__}: {e}"


# ============================================================
# The agent
# ============================================================

agent = Agent(
    name="ToolUsingAssistant",
    instructions=(
        "You are a helpful assistant with access to tools. "
        "When a question requires computation or external information, use "
        "the appropriate tool. After receiving results, give a clear, "
        "concise final answer."
    ),
    tools=[calculator, get_current_time, fetch_url],
)


# ============================================================
# Run it
# ============================================================


def main() -> None:
    prompts = [
        "What is 47 * 83 + 199?",
        "What time is it in Mumbai and Tokyo? What's the time difference in hours?",
        "Fetch https://hacker-news.firebaseio.com/v0/topstories.json and tell me the first 3 IDs.",
    ]

    for prompt in prompts:
        console.print(f"\n[bold]You:[/bold] {prompt}")
        result = Runner.run_sync(agent, prompt)
        console.print(f"\n[bold blue]Agent:[/bold blue] {result.final_output}\n")

        # Token usage and metrics
        usage = result.context_wrapper.usage
        console.print(
            f"[dim]Tokens: {usage.input_tokens} in / {usage.output_tokens} out | "
            f"Requests: {usage.requests}[/dim]"
        )
        console.print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
