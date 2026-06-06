"""Thin LLM helpers — Pydantic-typed calls for both Anthropic and OpenAI.

Not a framework. Just the minimal glue so we can focus on patterns
instead of boilerplate.
"""

from typing import TypeVar

from anthropic import Anthropic
from openai import OpenAI
from pydantic import BaseModel

from week2_agent_patterns.config import settings

T = TypeVar("T", bound=BaseModel)


def call_anthropic(
    prompt: str,
    schema: type[T],
    model: str = "claude-haiku-4-5-20251001",
    max_tokens: int = 2048,
    system: str | None = None,
) -> T:
    """Call Anthropic and force the response to match a Pydantic schema."""
    client = Anthropic(api_key=settings.anthropic_api_key)

    schema_tool = {
        "name": "return_result",
        "description": "Return the result in the required structure.",
        "input_schema": schema.model_json_schema(),
    }

    kwargs = {
        "model": model,
        "max_tokens": max_tokens,
        "tools": [schema_tool],
        "tool_choice": {"type": "tool", "name": "return_result"},
        "messages": [{"role": "user", "content": prompt}],
    }
    if system is not None:
        kwargs["system"] = system

    response = client.messages.create(**kwargs)
    tool_block = next(b for b in response.content if b.type == "tool_use")
    return schema.model_validate(tool_block.input)


def call_openai(
    prompt: str,
    schema: type[T],
    model: str = "gpt-4o-mini",
    system: str | None = None,
) -> T:
    """Call OpenAI and force the response to match a Pydantic schema."""
    client = OpenAI(api_key=settings.openai_api_key)

    messages = []
    if system is not None:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    response = client.beta.chat.completions.parse(
        model=model,
        messages=messages,
        response_format=schema,
    )
    parsed = response.choices[0].message.parsed
    if parsed is None:
        raise ValueError("OpenAI returned no parsed content")
    return parsed


def call_text_anthropic(
    prompt: str,
    model: str = "claude-haiku-4-5-20251001",
    max_tokens: int = 2048,
    system: str | None = None,
) -> str:
    """Call Anthropic, return plain text (no schema)."""
    client = Anthropic(api_key=settings.anthropic_api_key)

    kwargs = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }
    if system is not None:
        kwargs["system"] = system

    response = client.messages.create(**kwargs)
    return "".join(b.text for b in response.content if b.type == "text")
