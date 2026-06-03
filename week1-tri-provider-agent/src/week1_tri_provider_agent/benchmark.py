"""Benchmark the same agent task across Anthropic, OpenAI, and Gemini.

Measures wall-clock latency, token usage, and gives a side-by-side comparison.
Generates output suitable for screenshotting into a thread.
"""

import time

from rich.console import Console
from rich.table import Table

from week1_tri_provider_agent import agent as anthropic_agent
from week1_tri_provider_agent import openai_agent as openai_agent_module
from week1_tri_provider_agent import gemini_agent as gemini_agent_module


console = Console()


# Approximate pricing per 1M tokens — input / output USD
# Update these as providers change pricing
PRICING = {
    "claude-haiku-4-5": {"input": 1.00, "output": 5.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gemini-2.5-flash": {"input": 0.30, "output": 2.50},
}


def cost_for(model: str, input_tokens: int, output_tokens: int) -> float:
    """Calculate USD cost given model and token counts."""
    p = PRICING[model]
    return (input_tokens / 1_000_000) * p["input"] + (output_tokens / 1_000_000) * p[
        "output"
    ]


# ============================================================
# Wrapped versions of each agent that capture stats
# ============================================================


def run_anthropic_silent(prompt: str) -> dict:
    """Run the Anthropic agent, suppress console output, return stats."""
    from anthropic import Anthropic
    from week1_tri_provider_agent.config import settings
    from week1_tri_provider_agent.tools import TOOLS_SCHEMA, TOOL_IMPLEMENTATIONS

    client = Anthropic(api_key=settings.anthropic_api_key)
    messages = [{"role": "user", "content": prompt}]

    total_input = 0
    total_output = 0
    steps = 0

    for _ in range(10):
        steps += 1
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            system=anthropic_agent.SYSTEM_PROMPT,
            tools=TOOLS_SCHEMA,
            messages=messages,
        )
        total_input += response.usage.input_tokens
        total_output += response.usage.output_tokens
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            final = "".join(b.text for b in response.content if b.type == "text")
            return {
                "final": final,
                "steps": steps,
                "input_tokens": total_input,
                "output_tokens": total_output,
            }

        if response.stop_reason == "tool_use":
            results = []
            for b in response.content:
                if b.type == "tool_use":
                    impl = TOOL_IMPLEMENTATIONS[b.name]
                    result = impl(b.input)
                    results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": b.id,
                            "content": result,
                        }
                    )
            messages.append({"role": "user", "content": results})

    return {
        "final": "[max steps]",
        "steps": steps,
        "input_tokens": total_input,
        "output_tokens": total_output,
    }


def run_openai_silent(prompt: str) -> dict:
    """Same but for OpenAI."""
    import json as json_lib
    from openai import OpenAI
    from week1_tri_provider_agent.config import settings
    from week1_tri_provider_agent.openai_tools import (
        TOOLS_SCHEMA_OPENAI,
        TOOL_IMPLEMENTATIONS as OAI_IMPLS,
    )

    client = OpenAI(api_key=settings.openai_api_key)
    messages = [
        {"role": "system", "content": openai_agent_module.SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]

    total_input = 0
    total_output = 0
    steps = 0

    for _ in range(10):
        steps += 1
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=TOOLS_SCHEMA_OPENAI,
        )
        total_input += response.usage.prompt_tokens
        total_output += response.usage.completion_tokens

        message = response.choices[0].message
        finish = response.choices[0].finish_reason
        messages.append(message.model_dump(exclude_none=True))

        if finish == "stop":
            return {
                "final": message.content or "",
                "steps": steps,
                "input_tokens": total_input,
                "output_tokens": total_output,
            }

        if finish == "tool_calls":
            for tc in message.tool_calls:
                name = tc.function.name
                args = json_lib.loads(tc.function.arguments)
                result = OAI_IMPLS[name](args)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": result,
                    }
                )

    return {
        "final": "[max steps]",
        "steps": steps,
        "input_tokens": total_input,
        "output_tokens": total_output,
    }


def run_gemini_silent(prompt: str) -> dict:
    """Same but for Gemini."""
    from google import genai
    from google.genai import types
    from week1_tri_provider_agent.config import settings
    from week1_tri_provider_agent.gemini_tools import (
        TOOLS_GEMINI,
        TOOL_IMPLEMENTATIONS as GEM_IMPLS,
    )

    client = genai.Client(api_key=settings.google_api_key)
    contents = [types.Content(role="user", parts=[types.Part(text=prompt)])]
    config = types.GenerateContentConfig(
        system_instruction=gemini_agent_module.SYSTEM_PROMPT,
        tools=[TOOLS_GEMINI],
    )

    total_input = 0
    total_output = 0
    steps = 0

    for _ in range(10):
        steps += 1
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents,
            config=config,
        )
        usage = response.usage_metadata
        total_input += usage.prompt_token_count
        total_output += usage.candidates_token_count or 0

        candidate = response.candidates[0]
        contents.append(candidate.content)

        function_calls = [
            p.function_call for p in candidate.content.parts if p.function_call
        ]

        if not function_calls:
            final = "".join(p.text for p in candidate.content.parts if p.text)
            return {
                "final": final,
                "steps": steps,
                "input_tokens": total_input,
                "output_tokens": total_output,
            }

        tool_parts = []
        for fc in function_calls:
            result = GEM_IMPLS[fc.name](dict(fc.args))
            tool_parts.append(
                types.Part.from_function_response(
                    name=fc.name, response={"result": result}
                )
            )
        contents.append(types.Content(role="user", parts=tool_parts))

    return {
        "final": "[max steps]",
        "steps": steps,
        "input_tokens": total_input,
        "output_tokens": total_output,
    }


# ============================================================
# Benchmark driver
# ============================================================


def benchmark(prompt: str) -> None:
    """Run the same prompt across all three providers, measure, display."""
    console.print(f"\n[bold]Prompt:[/bold] {prompt}\n")

    runs = [
        ("Anthropic Claude Haiku 4.5", "claude-haiku-4-5", run_anthropic_silent),
        ("OpenAI GPT-4o-mini", "gpt-4o-mini", run_openai_silent),
        ("Google Gemini 2.5 Flash", "gemini-2.5-flash", run_gemini_silent),
    ]

    results = []
    for display_name, model_key, runner in runs:
        console.print(f"[dim]Running {display_name}...[/dim]")
        start = time.perf_counter()
        try:
            stats = runner(prompt)
            elapsed = time.perf_counter() - start
            results.append(
                {
                    "provider": display_name,
                    "model_key": model_key,
                    "elapsed": elapsed,
                    **stats,
                }
            )
        except Exception as e:
            results.append(
                {
                    "provider": display_name,
                    "model_key": model_key,
                    "error": str(e),
                }
            )

    # Build the comparison table
    table = Table(title="Tri-Provider Benchmark")
    table.add_column("Provider", style="bold")
    table.add_column("Time", justify="right")
    table.add_column("Steps", justify="right")
    table.add_column("In tokens", justify="right")
    table.add_column("Out tokens", justify="right")
    table.add_column("Cost (¢)", justify="right", style="green")

    for r in results:
        if "error" in r:
            table.add_row(r["provider"], "—", "—", "—", "—", f"ERR: {r['error'][:30]}")
            continue
        cost_cents = (
            cost_for(r["model_key"], r["input_tokens"], r["output_tokens"]) * 100
        )
        table.add_row(
            r["provider"],
            f"{r['elapsed']:.2f}s",
            str(r["steps"]),
            f"{r['input_tokens']:,}",
            f"{r['output_tokens']:,}",
            f"{cost_cents:.3f}",
        )

    console.print(table)

    # Print each final answer
    console.print("\n[bold]Final answers:[/bold]")
    for r in results:
        if "error" not in r:
            console.print(f"\n[bold cyan]{r['provider']}:[/bold cyan]")
            console.print(r["final"])


def main() -> None:
    prompts = [
        "What is 47 * 83 + 199?",
        "What time is it in Mumbai and Tokyo? What's the time difference in hours?",
        "Fetch https://hacker-news.firebaseio.com/v0/topstories.json and tell me the first 3 IDs.",
    ]

    for prompt in prompts:
        benchmark(prompt)
        console.print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
