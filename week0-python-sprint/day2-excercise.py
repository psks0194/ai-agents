from pydantic import BaseModel, Field
from typing import Literal
import json

class WebSearchTool(BaseModel):
    tool_name: Literal["web_search"] = "web_search"
    query: str = Field(..., min_length=1, max_length=200)
    max_results: int = Field(default=5, ge=1, le=10)
    region: Literal["US", "CA", "GB", "IN"] = "US"

class CalculatorTool(BaseModel):
    tool_name: Literal["calculator"] = "calculator"
    expression: str = Field(..., min_length=1, max_length=200)
    precision: int = Field(default=2, ge=0, le=10)


def execute_search(tool_call_json: str) -> str:
    # Step 1: Parse raw JSON to extract tool_name
    try:
        raw = json.loads(tool_call_json)
    except json.JSONDecodeError as e:
        return f"Error: Malformed JSON — {e}"

    tool_name = raw.get("tool_name")
    if not tool_name:
        return f"Error: Missing 'tool_name' in payload: {raw}"

    # Step 2: Validate against the correct Pydantic model
    try:
        if tool_name == "web_search":
            tool = WebSearchTool.model_validate_json(tool_call_json)
        elif tool_name == "calculator":
            tool = CalculatorTool.model_validate_json(tool_call_json)
        else:
            return f"Error: Unknown tool name: '{tool_name}'"
    except Exception as e:
        return f"Error validating '{tool_name}' tool call: {e}"    
    if tool_name == "web_search":
        return (
        f"Executing web search for: {tool.query}\n"
        f"Max results: {tool.max_results}, Region: {tool.region}\n"
        f"tool name: {tool.tool_name}\n"
    )
    elif tool_name == "calculator":
        return (
        f"Executing calculator for: {tool.expression}\n"
        f"Precision: {tool.precision}\n"
        f"tool name: {tool.tool_name}\n"
    )

# Test cases — like calls from an LLM
test_calls = [
    # Valid: minimal
    '{"tool_name": "web_search", "query": "weather in mumbai"}',

    # Valid: full
    '{"query": "rbi ppi 2026", "max_results": 10, "region": "in"}',

    # Invalid: empty query
    '{"query": ""}',

    # Invalid: max_results too high
    '{"query": "test", "max_results": 100}',

    # Invalid: unknown region
    '{"query": "test", "region": "antarctica"}',

    # Invalid: wrong tool_name (shouldn't be allowed)
    '{"tool_name": "delete_database", "query": "test"}',

    # Invalid: malformed JSON
    '{not valid json',

    # Valid: calculator tool call
    '{"tool_name": "calculator", "expression": "2 + 2"}',

    # Invalid: calculator tool call
    '{"tool_name": "calculator", "expression": "2 + 2", "precision": 100}',

    # Invalid: calculator tool call
    '{"tool_name": "calculator", "expression": "2 + 2", "precision": 100}',

    # Invalid: calculator tool call
    '{"tool_name": "calculator", "expression": "2 + 2", "precision": 100}',

    # Invalid: calculator tool call
    '{"tool_name": "calculator", "expression": "2 + 2", "precision": 100}',

    # Invalid: calculator tool call
    '{"tool_name": "calculator", "expression": "2 + 2", "precision": 100}',
]

for i, call in enumerate(test_calls, start=1):
    print(f"--- Test case {i} ---")
    print(f"Input: {call}")
    result = execute_search(call)
    print(result)
    print()


