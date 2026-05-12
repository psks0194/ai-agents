# Day 2 — Type Hints & Pydantic

Day 2 is about making Python data *trustworthy*. Python is dynamically typed: a variable can hold a string today and an integer tomorrow, and the interpreter shrugs. That flexibility is wonderful while prototyping and dangerous once your code talks to the outside world — APIs, user input, LLM tool calls. Today we add two layers of safety:

1. **Type hints** — annotations that document intent and let static checkers (Pylance, mypy) catch mistakes *before* runtime.
2. **Pydantic models** — runtime validators that reject bad data *at the boundary* of your program.

The three files in this directory map to three steps of that journey.

| File | What it teaches |
|------|-----------------|
| `day2_types.py` | The built-in type-hint vocabulary |
| `day2_pydantic.py` | Pydantic models — runtime-validated data classes |
| `day2-excercise.py` | A mini tool-dispatcher that validates JSON tool calls from an LLM |

---

## Part 1 — Type hints (`day2_types.py`)

### Why type hints?

A type hint is a promise about what a variable holds. The Python interpreter *ignores* hints at runtime — they exist for humans and tools. But that's enough to catch a huge class of bugs early.

```python
name: str = "Monica"
age: int = 25
height: float = 5.6
is_student: bool = True
nothing: None = None
```

The form is `name: type = value`. You can omit the value (just `name: str`) for declarations.

### Collection types

Built-in containers can be parameterized to say *what they hold*:

```python
skills: list[str] = ["Python", "Java", "C++"]
grades: dict[str, int] = {"Math": 90, "Science": 80}
coordinate: tuple[int, int] = (10, 20)
unique_tags: set[str] = {"Python", "Java"}
```

Before Python 3.9 you had to import `List`, `Dict`, etc. from `typing`. Modern Python lets you use the lowercase built-ins directly — much cleaner.

### Union types — "this OR that"

A value can have more than one allowed type. The modern syntax uses `|`:

```python
middle_name: str | None = None   # either a string or None
score: float | int = 88.5        # either float or int
```

`str | None` (often called *Optional*) is the most common union you'll see — it marks "this might be missing."

### Functions with hints

Hints really pay off in function signatures, where they document the contract:

```python
def find_user(user_id: int) -> dict[str, str] | None:
    fake_users = {
        101: {"name": "Alice", "email": "a@x.com"},
        102: {"name": "Bob",   "email": "b@x.com"},
    }
    return fake_users.get(user_id)
```

A reader (or your editor) immediately knows: pass an `int`, get back either a `dict[str, str]` or `None`. That return-type union *forces* the caller to handle the missing case:

```python
user = find_user(105)
if user is not None:
    print(user["name"])      # safe
else:
    print("User not found")
```

If you skip the `None` check, Pylance underlines `user["name"]` in red. The bug is caught before you ever run the code.

### Where type hints fall short

Hints are static — they describe what *should* be true. They cannot stop bad data from arriving at runtime:

```python
def filter_high_scorers(
    students: list[dict[str, int | str]],
    threshold: int = 80,
) -> list[str]:
    return [
        s["name"]
        for s in students
        if isinstance(s["score"], int) and s["score"] >= threshold
    ]

bad_students = [
    {"name": "Aarav", "score": "ninety-five"},  # score is a string
    {"name": "Priya"},                           # missing score
    {"name": 42, "score": 88},                   # name is an int
]
```

Pylance can't see inside that `list` literal — every dict matches the loose `dict[str, int | str]` hint. At runtime the function silently misbehaves or throws `KeyError`. We need something stronger at the boundary. Enter Pydantic.

---

## Part 2 — Pydantic (`day2_pydantic.py`)

### What Pydantic adds

Pydantic gives you a `BaseModel` class. Subclass it, declare fields with type hints, and you get for free:

- **Runtime validation** — wrong types are rejected with a clear error.
- **Coercion** — `"92"` becomes `92` when the field is `int` (configurable).
- **Serialization** — `.model_dump()` → dict, `.model_dump_json()` → JSON string.
- **Deserialization** — `Model.model_validate_json(s)` parses *and* validates in one step.

### A first model

```python
from pydantic import BaseModel

class Student(BaseModel):
    name: str
    score: int

alice = Student(name="Alice", score=95)
print(alice.name)    # "Alice"
print(alice.score)   # 95
```

So far it looks like a fancy dataclass. The magic shows up on bad input:

```python
Student(name="Bob", score="ninety-five")
# ValidationError: score — Input should be a valid integer,
#                  unable to parse string as an integer
```

And on input that *can* be coerced:

```python
charlie = Student(name="Charlie", score="92")
print(charlie.score)         # 92  (now an int)
print(type(charlie.score))   # <class 'int'>
```

Pydantic's default mode is "lax" — it tries to coerce sensibly. If you want strict mode, you can opt in per-field or per-model.

### Nested models

Real data is rarely flat. Pydantic composes:

```python
class Address(BaseModel):
    street: str
    city: str
    zip: str

class Person(BaseModel):
    name: str
    age: int
    address: Address

p = Person(
    name="Prashant",
    age=32,
    address={"street": "123 Main St", "city": "Anytown", "zip": "12345"},
)
print(p.address.city)   # "Anytown"
```

Notice the address came in as a plain dict — Pydantic automatically converted it to an `Address` instance because the field is typed as `Address`. This is the killer feature: deeply nested JSON validates and constructs in a single call.

### Optional fields and defaults

```python
class UserProfile(BaseModel):
    username: str
    email: str
    bio: str | None = None
    tags: list[str] = []
    follower_count: int = 0
    is_verified: bool = True
```

- `username` and `email` are **required** (no default).
- `bio` is **optional** — can be a string or absent (`None`).
- `tags`, `follower_count`, `is_verified` have defaults.

```python
user1 = UserProfile(username="Prashant", email="pras@gmail.com")
# bio=None, tags=[], follower_count=0, is_verified=True — all filled in
```

> **Gotcha:** using a mutable default like `tags: list[str] = []` would be a bug in plain Python (the list is shared between instances). Pydantic handles this safely — each instance gets a fresh copy.

### Serialization round-trip

```python
user_json = user2.model_dump_json()
# '{"username":"Priya","email":"priya@gmail.com",...}'

user_dict = user2.model_dump()
# {"username": "Priya", "email": "priya@gmail.com", ...}

parsed = UserProfile.model_validate_json(user_json)
# Back to a UserProfile instance — fully validated
```

`model_validate_json` is what you'll call when an LLM hands you a JSON tool call. It parses *and* validates in one atomic step, and raises if anything is wrong.

---

## Part 3 — The exercise (`day2-excercise.py`)

### The setup

Imagine an LLM is calling tools in your app. It emits JSON like:

```json
{"tool_name": "web_search", "query": "weather in mumbai", "max_results": 5}
```

You need to (a) figure out which tool it's calling, (b) validate the arguments, and (c) execute it. If the JSON is malformed or the arguments are wrong, you must fail *gracefully* — not crash the process.

### Defining tool schemas

```python
from pydantic import BaseModel, Field
from typing import Literal

class WebSearchTool(BaseModel):
    tool_name: Literal["web_search"] = "web_search"
    query: str = Field(..., min_length=1, max_length=200)
    max_results: int = Field(default=5, ge=1, le=10)
    region: Literal["US", "CA", "GB", "IN"] = "US"

class CalculatorTool(BaseModel):
    tool_name: Literal["calculator"] = "calculator"
    expression: str = Field(..., min_length=1, max_length=200)
    precision: int = Field(default=2, ge=0, le=10)
```

Three new ideas show up here:

- **`Literal["web_search"]`** — the field can only hold the exact string `"web_search"`. Any other value is rejected. This is how we identify which tool was called.
- **`Field(...)`** — extra constraints beyond the type. `...` (ellipsis) means "required, no default." `min_length`, `max_length`, `ge` (≥), `le` (≤) add validation rules.
- **Per-tool models** — one Pydantic class per tool. The schema *is* the contract.

### The dispatcher

```python
def execute_search(tool_call_json: str) -> str:
    # Step 1: Parse the JSON so we can read tool_name
    try:
        raw = json.loads(tool_call_json)
    except json.JSONDecodeError as e:
        return f"Error: Malformed JSON — {e}"

    tool_name = raw.get("tool_name")
    if not tool_name:
        return f"Error: Missing 'tool_name' in payload: {raw}"

    # Step 2: Validate against the right model
    try:
        if tool_name == "web_search":
            tool = WebSearchTool.model_validate_json(tool_call_json)
        elif tool_name == "calculator":
            tool = CalculatorTool.model_validate_json(tool_call_json)
        else:
            return f"Error: Unknown tool name: '{tool_name}'"
    except Exception as e:
        return f"Error validating '{tool_name}' tool call: {e}"

    # Step 3: Execute (here, just format the response)
    if tool_name == "web_search":
        return f"Executing web search for: {tool.query} ..."
    elif tool_name == "calculator":
        return f"Executing calculator for: {tool.expression} ..."
```

The flow has three guard rails:

1. **JSON parse** — catches malformed payloads (`'{not valid json'`).
2. **Tool lookup** — catches unknown tools (`'{"tool_name": "delete_database", ...}'` is rejected; we never dispatch to something we didn't whitelist).
3. **Pydantic validation** — catches bad arguments (`max_results: 100` when the cap is 10, empty `query`, unknown `region`).

Notice the dispatcher *returns* error strings instead of raising. That's deliberate: an LLM tool-calling loop should report the error back to the model so it can self-correct, not crash the whole agent.

### What the test cases prove

The `test_calls` list walks through every failure mode:

| Case | What it tests |
|------|---------------|
| Minimal valid call | Defaults fill in (`max_results=5`, `region="US"`) |
| Full valid call | All fields honored |
| Empty query | `min_length=1` fires |
| `max_results: 100` | `le=10` fires |
| `region: "antarctica"` | `Literal` rejects unknown values |
| `tool_name: "delete_database"` | Whitelist rejects |
| Malformed JSON | `json.JSONDecodeError` caught |
| Valid calculator call | Second model branches correctly |

This is the pattern you'll use anywhere untrusted JSON enters your program: parse → identify → validate-with-schema → execute.

---

## Takeaways

1. **Type hints document; Pydantic enforces.** Use hints everywhere. Use Pydantic at every boundary (API request, file load, LLM response).
2. **`Literal` + `Field` are the workhorses.** Together they encode "must be one of these exact values" and "must satisfy this constraint" — most real-world validation collapses to these two patterns.
3. **Per-tool / per-shape models beat one big union.** When you have multiple JSON shapes (different tools, different event types), give each its own model and dispatch on a discriminator field.
4. **Fail with a message, not an exception.** At system boundaries, convert errors into structured responses so the caller (whether a user, another service, or an LLM) can react sensibly.

## Running

```bash
uv run day2_types.py
uv run day2_pydantic.py
uv run day2-excercise.py
```
