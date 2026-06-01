"""Gemini tool-using agent — third port of the loop.

Notice: the loop structure is identical to Anthropic and OpenAI versions.
Only the vocabulary changes.
"""

from google import genai
from google.genai import types
from rich.console import Console

from week1_tri_provider_agent.config import settings
from week1_tri_provider_agent.gemini_tools import TOOLS_GEMINI, TOOL_IMPLEMENTATIONS


console = Console()
MODEL = "gemini-2.5-flash"
MAX_STEPS = 10

SYSTEM_PROMPT = (
    "You are a helpful assistant with access to tools. "
    "When a user's question requires computation or external information, "
    "use the appropriate tool. After receiving tool results, give a clear, "
    "concise final answer."
)


def run_tool(tool_name: str, tool_input: dict) -> str:
    """Dispatch a tool call to its implementation."""
    impl = TOOL_IMPLEMENTATIONS.get(tool_name)
    if impl is None:
        return f"Error: unknown tool '{tool_name}'"
    try:
        return impl(tool_input)
    except Exception as e:
        return f"Error executing {tool_name}: {type(e).__name__}: {e}"


def run_agent(user_message: str) -> str:
    """Run the Gemini agent loop until a final answer."""
    client = genai.Client(api_key=settings.google_api_key)

    # Gemini's `contents` is a list of Content objects, each with role + parts.
    # We manage this list ourselves to get the same explicit control as
    # Anthropic and OpenAI loops.
    contents: list[types.Content] = [
        types.Content(role="user", parts=[types.Part(text=user_message)])
    ]

    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        tools=[TOOLS_GEMINI],
    )

    for step in range(MAX_STEPS):
        console.print(f"\n[dim]--- step {step + 1} ---[/dim]")

        response = client.models.generate_content(
            model=MODEL,
            contents=contents,
            config=config,
        )

        # Gemini puts everything in candidates[0].content.parts
        candidate = response.candidates[0]
        finish_reason = candidate.finish_reason
        usage = response.usage_metadata

        console.print(
            f"[dim]finish_reason: {finish_reason}, "
            f"tokens: {usage.prompt_token_count}/{usage.candidates_token_count}[/dim]"
        )

        # Append the model's response to the conversation
        contents.append(candidate.content)

        # Check if any of the parts is a function call
        function_calls = [
            part.function_call
            for part in candidate.content.parts
            if part.function_call is not None
        ]

        if not function_calls:
            # No tool calls — extract final text and we're done
            final_text = "".join(
                part.text for part in candidate.content.parts if part.text is not None
            )
            return final_text

        # Execute each function call and build response parts
        tool_response_parts = []
        for fc in function_calls:
            tool_name = fc.name
            tool_input = dict(fc.args)  # fc.args is a MapComposite; convert to dict

            console.print(
                f"[yellow]→ tool call:[/yellow] [bold]{tool_name}[/bold]({tool_input})"
            )
            result = run_tool(tool_name, tool_input)
            console.print(f"[green]← result:[/green] {result}")

            tool_response_parts.append(
                types.Part.from_function_response(
                    name=tool_name,
                    response={"result": result},
                )
            )

        # Send tool results back as a user-role Content with function_response parts
        contents.append(types.Content(role="user", parts=tool_response_parts))

    return "[Agent hit max steps without completing]"


def main() -> None:
    console.print(
        "[bold cyan]Gemini tool-using agent.[/bold cyan] Type 'exit' to quit.\n"
    )

    while True:
        user_input = console.input("[bold green]you:[/bold green] ").strip()
        if user_input.lower() in ("exit", "quit"):
            break
        if not user_input:
            continue

        final = run_agent(user_input)
        console.print(f"\n[bold blue]agent:[/bold blue] {final}\n")


if __name__ == "__main__":
    main()
