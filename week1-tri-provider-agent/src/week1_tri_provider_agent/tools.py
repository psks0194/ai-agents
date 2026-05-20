"""Tools that Claude can call.

Each tool has two parts:
1. The schema (a dict) — what Claude sees when deciding to call it
2. The implementation (a Python function) — what actually runs

We keep both in one place per tool for clarity.
"""

import httpx
from typing import Any
from datetime import datetime
from zoneinfo import ZoneInfo


# ============================================================
# Tool 1: Calculator
# ============================================================

CALCULATOR_TOOL = {
    "name": "calculator",
    "description": (
        "Evaluate a basic mathematical expression. "
        "Supports +, -, *, /, **, and parentheses. "
        "Use this whenever you need to compute a numeric result."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "A math expression like '47 * 83 + 199' or '(5 + 3) ** 2'",
            }
        },
        "required": ["expression"],
    },
}


def run_calculator(expression: str) -> str:
    """Execute the calculator. Returns the result as a string."""
    # eval() is dangerous in general — but we restrict the namespace here.
    # Production code would use a proper expression parser.
    try:
        result = eval(expression, {"__builtins__": {}}, {})
        return str(result)
    except Exception as e:
        return f"Error: {type(e).__name__}: {e}"


# ============================================================
# Tool 2: Current time in a timezone
# ============================================================


CURRENT_TIME_TOOL = {
    "name": "get_current_time",
    "description": (
        "Get the current date and time in a specified IANA timezone. "
        "Use this when the user asks about the current time, today's date, "
        "or anything time-sensitive. Returns ISO format with timezone."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "timezone": {
                "type": "string",
                "description": (
                    "IANA timezone name, e.g. 'Asia/Kolkata', 'America/New_York', "
                    "'Europe/London', 'UTC'. Default 'UTC' if user gave no preference."
                ),
            }
        },
        "required": ["timezone"],
    },
}


def run_current_time(timezone: str) -> str:
    try:
        now = datetime.now(ZoneInfo(timezone))
        return now.isoformat()
    except Exception as e:
        return f"Error: {type(e).__name__}: {e}"


# ============================================================
# Tool 3: Web fetch
# ============================================================

WEB_FETCH_TOOL = {
    "name": "fetch_url",
    "description": (
        "Fetch the contents of a web page. Returns the first 2000 characters of "
        "the page text. Use when you need current information from a specific URL "
        "the user has provided, or when explicitly asked to look something up online. "
        "Do not invent URLs — only fetch URLs the user has given or that you have "
        "high confidence exist."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "The full URL to fetch, including https://",
            }
        },
        "required": ["url"],
    },
}


def run_fetch_url(url: str) -> str:
    try:
        with httpx.Client(timeout=10.0, follow_redirects=True) as client:
            response = client.get(
                url,
                headers={"User-Agent": "week1-agent/0.1"},
            )
            response.raise_for_status()
            text = response.text[:6000]
            return f"URL: {url}\nStatus: {response.status_code}\n\n{text}"
    except Exception as e:
        return f"Error fetching {url}: {type(e).__name__}: {e}"


# ============================================================
# Registry: name -> implementation
# ============================================================

TOOLS_SCHEMA: list[dict[str, Any]] = [
    CALCULATOR_TOOL,
    CURRENT_TIME_TOOL,
    WEB_FETCH_TOOL,
]

TOOL_IMPLEMENTATIONS: dict[str, Any] = {
    "calculator": lambda args: run_calculator(args["expression"]),
    "get_current_time": lambda args: run_current_time(args["timezone"]),
    "fetch_url": lambda args: run_fetch_url(args["url"]),
}
