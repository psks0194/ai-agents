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

## Status (Day 1 — 2026-07-03)

- ✅ Server object — `FastMCP("IntellAIgent_Content_Ops")`, named `mcp` for zero-config install (`server.py`)
- ✅ First tool — `fetch_feed`, pulls an RSS/Atom feed into structured, LLM-friendly items (`server.py`)

## Layout

```
src/intellaigent_mcp/
  server.py     # the MCP server: server object + @mcp.tool definitions
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
   tool-definition schemas from Weeks 1–2 — just authored declaratively.
3. **Return types** — return plain dicts / dataclass dicts; FastMCP serializes them
   to JSON for the client. `fetch_feed` returns a `list[dict]` of `FeedItem`s.
4. **Transport** — `mcp.run()` uses **stdio** by default (the client spawns the
   server as a subprocess and talks over stdin/stdout). Resources and prompts —
   the other two MCP primitives — come in later days.

## Current tools

- **`fetch_feed(feed_url, limit=8)`** — fetch an RSS/Atom feed and return recent
  items (`title`, `summary`, `link`, `published`) as structured data. Sends an
  explicit User-Agent (some feeds `403` a blank one) and clamps `limit` to 1–25.
