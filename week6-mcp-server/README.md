# week6-mcp-server

The final inversion: instead of *writing* an agent that calls tools, we **build
the tools** — an **MCP server** that any agent can drive. Weeks 1–5 put the model
in the driver's seat and handed it functions; here we sit on the other side of the
protocol and expose the IntellAIgent content pipeline as MCP **tools**, **resources**,
and **prompts** so any MCP client (Claude Code, Claude Desktop) can compose it.

The throughline from the whole curriculum: an agent is a loop (`call → tool →
result → call → final answer`). MCP is the standard wire format for the *tool*
half of that loop — it decouples the tools from any one agent or framework. Built
with **FastMCP 3**, the Pythonic way to author MCP servers.

## Status

**Day 1 — 2026-07-03**

- ✅ Server object — `FastMCP("IntellAIgent_Content_Ops")`, named `mcp` for zero-config install (`server.py`)
- ✅ First tool — `fetch_feed`, pulls an RSS/Atom feed into structured, LLM-friendly items (`server.py`)

**Day 2 — 2026-07-05**

- ✅ Typed I/O — Pydantic output models (`CardSpec`, `VoiceReport`, `ThreadDraft`) so clients get structured, addressable data, not opaque text (`models.py`)
- ✅ Settings — `pydantic-settings` reads the repo-root `.env` for `ANTHROPIC_API_KEY` + `default_model` (`config.py`)
- ✅ `generate_card_spec` — resolves the brand palette/grid/footer into a 1600×900 card spec (`server.py`)
- ✅ `check_voice` — lints text against the voice rules: hype words, hedges, intensifiers (`server.py`)
- ✅ `draft_thread` — the first **LLM-backed** tool: calls Anthropic to draft a thread, streaming progress via `Context` (`server.py`)
- ✅ End-to-end run — `fetch_feed → draft_thread → check_voice → generate_card_spec` composed from an MCP client

## Layout

```
src/intellaigent_mcp/
  server.py     # the MCP server: server object + @mcp.tool definitions
  models.py     # Pydantic output models (typed tool results → output schemas)
  config.py     # pydantic-settings: ANTHROPIC_API_KEY + default_model from repo .env
main.py         # placeholder entrypoint (unused by the server)
```

## Commands

This week uses `uv` and its own `.venv`. Run from `week6-mcp-server/`. If another
venv is active (e.g. `hntop`), `deactivate` first — `uv run` targets this project's
`.venv`, and a mismatched `VIRTUAL_ENV` only produces a warning, but the tooling is
clearer from a clean shell.

```bash
# Run the server directly (stdio transport)
uv run fastmcp run src/intellaigent_mcp/server.py

# Develop with the MCP Inspector UI in the browser
uv run fastmcp dev inspector src/intellaigent_mcp/server.py

# Install into Claude Code
uv run fastmcp install claude-code src/intellaigent_mcp/server.py

# Inspect the server's tools/resources without running a client
uv run fastmcp inspect src/intellaigent_mcp/server.py
```

> **FastMCP 3.x note:** `fastmcp dev` is now a *command group*, not a direct
> runner. The old `fastmcp dev <file>` was split — the MCP Inspector moved under
> `fastmcp dev inspector <file>`. Running `fastmcp dev <file>` errors with
> `Unknown command … Available commands: inspector, apps`.

## Core concepts

FastMCP has a small surface:

1. **The server object** — `mcp = FastMCP("name")`. Naming it `mcp` (or `server` /
   `app`) lets `fastmcp install` auto-discover it, so no `:object` suffix is needed.
2. **`@mcp.tool`** — decorates a plain function into an MCP tool. The docstring +
   type hints become the schema the client's model sees, exactly like the raw
   tool-definition schemas from Weeks 1–2 — just authored declaratively. `async`
   tools (`draft_thread`) are supported directly.
3. **Return types** — return plain dicts / dataclass dicts, or a **Pydantic model**.
   FastMCP turns a model's fields into an *output schema*, so `generate_card_spec`,
   `check_voice`, and `draft_thread` hand the client typed, addressable results
   (`models.py`) — the typed-boundary discipline from the agent weeks, at the
   protocol edge. `fetch_feed` returns a `list[dict]` of `FeedItem`s.
4. **`Context`** — a tool that declares a `ctx: Context` parameter can log and
   report progress back to the client mid-call. `draft_thread` uses `ctx.info`
   and `ctx.report_progress` around its model call.
5. **Errors** — raise `ToolError` for a clean, client-visible failure (e.g. a
   too-long headline, or a missing `ANTHROPIC_API_KEY`).
6. **Transport** — `mcp.run()` uses **stdio** by default (the client spawns the
   server as a subprocess and talks over stdin/stdout). Resources and prompts —
   the other two MCP primitives — come in later days.

## Current tools

- **`fetch_feed(feed_url, limit=8)`** — fetch an RSS/Atom feed and return recent
  items (`title`, `summary`, `link`, `published`) as structured data. Sends an
  explicit User-Agent (some feeds `403` a blank one) and clamps `limit` to 1–25.
- **`draft_thread(source_title, source_summary, angle, num_tweets=6)`** — the one
  LLM-backed tool: calls Anthropic (`default_model`, default `claude-haiku-4-5`)
  to draft an X thread in the practitioner-contrarian voice, then parses `N/` lines
  into a `ThreadDraft`. Clamps `num_tweets` to 3–10 and reports progress via `Context`.
- **`check_voice(text)`** — lints text against the voice rules (hype words, hedges,
  empty intensifiers) and returns a `VoiceReport` with per-issue `term` + `suggestion`.
  Pure/deterministic — no model call.
- **`generate_card_spec(headline, subtitle, accent="cyan", eyebrow="Dispatch")`** —
  resolves the IntellAIgent palette, grid, and footer into a 1600×900 `CardSpec` for
  the Playwright/Chromium renderer. `accent` is one of `cyan | magenta | amber`;
  headlines over 90 chars raise a `ToolError` so they don't break the layout.

These compose end-to-end: `fetch_feed` for source → `draft_thread` for the copy →
`check_voice` to lint it → `generate_card_spec` for the visual.

## Configuration

`draft_thread` needs `ANTHROPIC_API_KEY`. `config.py` uses `pydantic-settings` to
read the **single repo-root `.env`** (shared across every Python week), plus an
optional `DEFAULT_MODEL` override. The other three tools run without any key.
