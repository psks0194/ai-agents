"""Multi-agent customer support with handoffs.

A triage agent routes to billing or technical specialists. Specialists can
hand back to triage if the topic shifts. The agents decide handoffs themselves
via natural-language instructions — the framework manages control transfer.

This is the OpenAI Agents SDK signature feature. Compare to Week 2 Day 2
routing, where YOUR code dispatched to specialists.
"""

from agents import Agent, Runner, set_default_openai_key
from rich.console import Console
from rich.panel import Panel
from week4_openai_mastra.config import settings


console = Console()
set_default_openai_key(settings.openai_api_key)

# ============================================================
# Specialist agents — defined first so triage can reference them
# ============================================================

billing_agent = Agent(
    name="BillingAgent",
    handoff_description="Handles payments, refunds, subscriptions, and invoice questions.",
    instructions=(
        "You are a billing specialist for a fintech payments product. "
        "Help with payment failures, refund requests, subscription changes, "
        "and invoice questions. Be precise about what you can and can't do. "
        "For refunds over $500, explain that a human agent must approve. "
        "If the user's question becomes technical (API errors, integration "
        "bugs), hand off back to the triage agent so they can be routed "
        "to technical support."
    ),
)


technical_agent = Agent(
    name="TechnicalAgent",
    handoff_description="Handles API errors, integration issues, bugs, and technical setup.",
    instructions=(
        "You are a technical support specialist for a fintech payments API. "
        "Help with API errors, webhook issues, integration problems, and "
        "SDK questions. Be concrete: reference specific error codes, suggest "
        "specific debugging steps. If the user's question becomes about "
        "billing or refunds, hand off back to the triage agent."
    ),
)


# ============================================================
# Triage agent — the entry point, hands off to specialists
# ============================================================

triage_agent = Agent(
    name="TriageAgent",
    instructions=(
        "You are the first point of contact for customer support at a fintech "
        "payments product. Your job is to understand what the user needs and "
        "hand off to the right specialist:\n"
        " - Billing questions (payments, refunds, subscriptions) → BillingAgent\n"
        " - Technical questions (API, webhooks, bugs, integration) → TechnicalAgent\n\n"
        "Greet the user briefly, understand their issue, then hand off. "
        "Don't try to solve specialist problems yourself — hand off promptly. "
        "If the issue is genuinely simple and general, you may answer directly."
    ),
    handoffs=[billing_agent, technical_agent],
)


# Wire the return handoffs — specialists can hand back to triage.
# We do this after triage is defined to avoid a circular reference.
billing_agent.handoffs = [triage_agent]
technical_agent.handoffs = [triage_agent]


# ============================================================
# Run a conversation
# ============================================================


def run_support(user_message: str) -> None:
    """Run the support system on a user message, showing the handoff trace."""
    console.print(f"\n[bold]User:[/bold] {user_message}\n")

    result = Runner.run_sync(triage_agent, user_message)

    # Show which agent ended up handling it
    console.print(
        Panel(
            result.final_output,
            title=f"Final response (handled by: {result.last_agent.name})",
            border_style="green",
        )
    )

    # Show the handoff trace — which agents were involved
    console.print("\n[bold]Agent trace:[/bold]")
    for item in result.new_items:
        item_type = type(item).__name__
        if "Handoff" in item_type:
            console.print("  [yellow]→ handoff occurred[/yellow]")
        elif "MessageOutput" in item_type:
            # Identify which agent produced output
            console.print("  [dim]message output[/dim]")

    usage = result.context_wrapper.usage
    console.print(
        f"\n[dim]Tokens: {usage.input_tokens} in / {usage.output_tokens} out | "
        f"Requests: {usage.requests}[/dim]"
    )


def main() -> None:
    test_messages = [
        "I was charged twice for my subscription this month. Can I get a refund?",
        "Your webhook keeps returning a 401 error even though my API key is valid.",
        "Hi, I have a question about my account.",
    ]

    for msg in test_messages:
        run_support(msg)
        console.print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
