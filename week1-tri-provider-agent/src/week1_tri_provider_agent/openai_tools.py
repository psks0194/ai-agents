"""OpenAI tool schemas — same tools, different schema wrapper.

The implementations live in tools.py and don't change.
Only the schema format differs between providers.
"""

from typing import Any

from week1_tri_provider_agent.tools import (
    run_calculator,
    run_current_time,
    run_fetch_url,
)

# OpenAI wraps each tool in {"type": "function", "function": {...}}
# That extra wrapper allows for future tool types beyond functions.

CALCULATOR_TOOL_OPENAI = {
    "type": "function",
    "function": {
        "name": "calculator",
        "description": (
            "Evaluate a basic mathematical expression. "
            "Supports +, -, *, /, **, and parentheses. "
            "Use this whenever you need to compute a numeric result."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "A math expression like '47 * 83 + 199' or '(5 + 3) ** 2'",
                }
            },
            "required": ["expression"],
        },
    },
}


CURRENT_TIME_TOOL_OPENAI = {
    "type": "function",
    "function": {
        "name": "get_current_time",
        "description": (
            "Get the current date and time in a specified IANA timezone. "
            "Use this when the user asks about the current time, today's date, "
            "or anything time-sensitive."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "timezone": {
                    "type": "string",
                    "description": "IANA timezone, e.g. 'Asia/Kolkata', 'UTC'",
                }
            },
            "required": ["timezone"],
        },
    },
}


WEB_FETCH_TOOL_OPENAI = {
    "type": "function",
    "function": {
        "name": "fetch_url",
        "description": (
            "Fetch the contents of a web page. Returns the first 5000 characters of "
            "the page. Use when you need current information from a specific URL."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The full URL to fetch, including https://",
                }
            },
            "required": ["url"],
        },
    },
}

TOOLS_SCHEMA_OPENAI = [
    CALCULATOR_TOOL_OPENAI,
    CURRENT_TIME_TOOL_OPENAI,
    WEB_FETCH_TOOL_OPENAI,
]

TOOL_IMPLEMENTATIONS: dict[str, Any] = {
    "calculator": lambda args: run_calculator(args["expression"]),
    "get_current_time": lambda args: run_current_time(args["timezone"]),
    "fetch_url": lambda args: run_fetch_url(args["url"]),
}
