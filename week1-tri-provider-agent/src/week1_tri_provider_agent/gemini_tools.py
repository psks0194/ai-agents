"""Gemini tool schemas.

Gemini wraps tools as FunctionDeclaration objects.
Different shape from both Anthropic and OpenAI.
The implementations are still the same Python functions from tools.py.
"""

from typing import Any
from google.genai import types

from week1_tri_provider_agent.tools import (
    run_calculator,
    run_current_time,
    run_fetch_url,
)


CALCULATOR_DECLARATION = types.FunctionDeclaration(
    name="calculator",
    description=(
        "Evaluate a basic mathematical expression. "
        "Supports +, -, *, /, **, and parentheses. "
        "Use this whenever you need to compute a numeric result."
    ),
    parameters={
        "type": "OBJECT",
        "properties": {
            "expression": {
                "type": "STRING",
                "description": "A math expression like '47 * 83 + 199' or '(5 + 3) ** 2'",
            },
        },
        "required": ["expression"],
    },
)


CURRENT_TIME_DECLARATION = types.FunctionDeclaration(
    name="get_current_time",
    description=(
        "Get the current date and time in a specified IANA timezone. "
        "Use this when the user asks about the current time, today's date, "
        "or anything time-sensitive."
    ),
    parameters={
        "type": "OBJECT",
        "properties": {
            "timezone": {
                "type": "STRING",
                "description": "IANA timezone, e.g. 'Asia/Kolkata', 'UTC'",
            },
        },
        "required": ["timezone"],
    },
)


WEB_FETCH_DECLARATION = types.FunctionDeclaration(
    name="fetch_url",
    description=(
        "Fetch the contents of a web page. Returns the first 5000 characters of "
        "the page. Use when you need current information from a specific URL."
    ),
    parameters={
        "type": "OBJECT",
        "properties": {
            "url": {
                "type": "STRING",
                "description": "The full URL to fetch, including https://",
            },
        },
        "required": ["url"],
    },
)


# Gemini wraps function declarations inside a Tool object
TOOLS_GEMINI = types.Tool(
    function_declarations=[
        CALCULATOR_DECLARATION,
        CURRENT_TIME_DECLARATION,
        WEB_FETCH_DECLARATION,
    ]
)


# Same implementations — only schemas differ across providers
TOOL_IMPLEMENTATIONS: dict[str, Any] = {
    "calculator": lambda args: run_calculator(args["expression"]),
    "get_current_time": lambda args: run_current_time(args["timezone"]),
    "fetch_url": lambda args: run_fetch_url(args["url"]),
}
