"""A from-scratch tracing layer: spans, nesting, structured attributes.

The primitives every observability tool shares:
- Span: a named, timed operation with attributes
- nesting via a context variable (async-safe current-parent tracking)
- Trace: the tree of spans for one run, dumpable to JSON for inspection

This is deliberately tiny. Phase 6 maps it onto OpenTelemetry's GenAI
conventions — the shape is the same, the chrome differs.
"""

from __future__ import annotations

import json
import time
import uuid
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Span:
    name: str
    span_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    start: float = field(default_factory=time.time)
    end: float | None = None
    attributes: dict[str, Any] = field(default_factory=dict)
    children: list["Span"] = field(default_factory=list)

    @property
    def duration_s(self) -> float:
        return (self.end or time.time()) - self.start

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "span_id": self.span_id,
            "duration_s": round(self.duration_s, 3),
            "attributes": self.attributes,
            "children": [c.to_dict() for c in self.children],
        }


# The async-safe pointer to "the currently open span". contextvars (not a
# global) so concurrent runs don't corrupt each other's nesting.
_current_span: ContextVar[Span | None] = ContextVar("current_span", default=None)


class Tracer:
    """Collects one trace (a tree of spans) per run."""

    def __init__(self, run_name: str):
        self.root = Span(name=run_name)
        self.root_token = _current_span.set(self.root)

    @contextmanager
    def span(self, name: str, **attributes: Any):
        """Open a child span under the current span; restore parent on exit."""
        parent = _current_span.get()
        s = Span(name=name, attributes=dict(attributes))
        (parent.children if parent else self.root.children).append(s)
        token = _current_span.set(s)
        try:
            yield s
        except Exception as e:
            s.attributes["error"] = f"{type(e).__name__}: {e}"
            raise
        finally:
            s.end = time.time()
            _current_span.reset(token)

    def finish(self) -> Span:
        self.root.end = time.time()
        _current_span.reset(self.root_token)
        return self.root

    def save(self, directory: str = "traces") -> Path:
        """Persist the trace as JSON — the artifact you debug from later."""
        Path(directory).mkdir(exist_ok=True)
        path = Path(directory) / f"{self.root.name}-{self.root.span_id}.json"
        path.write_text(json.dumps(self.root.to_dict(), indent=2))
        return path

    def print_tree(self) -> None:
        """Console rendering of the span tree with timings and key attributes."""

        def walk(s: Span, depth: int) -> None:
            pad = "  " * depth
            attrs = {k: v for k, v in s.attributes.items() if k != "output"}
            attr_str = f"  {attrs}" if attrs else ""
            print(f"{pad}▸ {s.name}  [{s.duration_s:.2f}s]{attr_str}")
            for c in s.children:
                walk(c, depth + 1)

        walk(self.root, 0)
