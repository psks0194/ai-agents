# week4-mastra

The agent patterns one more time — a **fourth** framework: **Mastra** (TypeScript).
Same throughline as the rest of the curriculum: *an agent is a loop* (`call → tool
→ result → call → final answer`). Each framework just hides or exposes that loop
differently. Mastra's stance: **you declare an `Agent` with its `tools`, and the
framework runs the loop for you** — much like the OpenAI Agents SDK, but in TS and
with a built-in model router, Studio UI, scorers, and observability.

## Status (Day 1 — 2026-06-24)

- ✅ Tool-using agent — calculator / current-time / fetch-url, the canonical tool-use loop in Mastra (`agents/tool-agent.ts`)
- ✅ Three utility tools defined with `createTool` + Zod schemas (`tools/utility-tool.ts`)
- ✅ Standalone runner that drives the agent over a few prompts (`run-tool-agent.ts`)
- ✅ Agent registered in the Mastra instance (`mastra/index.ts`)
- ✅ Debugged it end-to-end — four separate fixes (see **Issues fixed today**)

This sits alongside the bootstrapped weather example (`weather-agent`,
`weather-tool`, `weather-workflow`, `weather-scorer`) that ships with a new Mastra
project. Today's work is the **tool agent** and getting it to actually run.

## The tool agent

The same calculator / time / fetch-url loop built in Week 1 (raw Anthropic SDK),
Week 3 (Pydantic AI), and Week 4's OpenAI SDK — now in Mastra:

- **Week 1**: raw Anthropic SDK — *you* write the ~80-line loop.
- **Week 3**: Pydantic AI — `@agent.tool`, loop hidden.
- **Week 4 / OpenAI SDK**: `@function_tool`, `Runner` manages the loop.
- **Week 4 / Mastra**: `createTool(...)`, attach via `tools: {…}`, the `Agent`
  runs the loop. `agent.generate(prompt)` returns the final text plus usage.

### Tools — `tools/utility-tool.ts`

Each tool is a `createTool({ id, description, inputSchema, outputSchema, execute })`.
The `description` + Zod `inputSchema` become the schema the model sees. Three tools:

| Tool | id | What it does |
|---|---|---|
| `calculatorTool` | `calculator` | Evaluates a math expression via a restricted `Function(...)` |
| `currentTimeTool` | `get-current-time` | Current time for an IANA timezone |
| `fetchUrlTool` | `fetch-url` | Fetches a URL, returns the first 5000 chars |

> **API note:** in this Mastra version (`@mastra/core` ^1.46), `execute` receives
> the validated input **directly** — `execute: async ({ expression }) => …` — *not*
> wrapped in a `{ context }` object. This matches the bootstrapped `weather-tool.ts`.

### Agent — `agents/tool-agent.ts`

```ts
export const toolAgent = new Agent({
  id: "tool-agent",
  name: "Tool Using Assistant",
  instructions: "… use the appropriate tool … give a clear, concise final answer.",
  model: "anthropic/claude-haiku-4-5",
  tools: { calculatorTool, currentTimeTool, fetchUrlTool },
});
```

Two Mastra-specific things to notice:

1. **Model router string.** `model: "anthropic/claude-haiku-4-5"` — Mastra resolves
   the provider/model through its built-in **models.dev gateway**. No per-agent
   `api_key=` and no `@ai-sdk/anthropic` import; the gateway reads
   `process.env.ANTHROPIC_API_KEY` *lazily, at request time*.
2. **Registration.** Every agent must be registered in the Mastra instance
   (`mastra/index.ts`) to be reachable via `mastra.getAgent('toolAgent')` and to
   show up in Studio.

### Runner — `run-tool-agent.ts`

A standalone script (run with `tsx`) that fetches the agent and loops over three
prompts — one per tool — printing the answer, elapsed time, and token usage.

> **`import 'dotenv/config'` is required at the top.** Running a script directly
> with `tsx` does **not** load `.env`. The model router reads
> `process.env.ANTHROPIC_API_KEY` at request time, so without dotenv the gateway
> throws *"Could not find API key process.env.ANTHROPIC_API_KEY"* even though the
> key is sitting in `.env`. (`mastra dev`/`mastra build` load `.env` on their own;
> a raw `tsx` invocation does not.)

## Issues fixed today

Getting the tool agent from "written" to "running" took four fixes:

| # | Symptom | Cause | Fix |
|---|---|---|---|
| 1 | Model import wouldn't resolve | `import { anthropic } from "@mastra/core/llm"` + `anthropic(...)` — not a usable API here, and no `@ai-sdk/anthropic` installed | Use the model-router string `model: "anthropic/claude-haiku-4-5"` |
| 2 | Tools import failed | Imported from `../tools/utility-tools` (plural) | File is `utility-tool.ts` (singular) |
| 3 | Agent unreachable | Not registered in the Mastra instance | Add to `agents: { weatherAgent, toolAgent }` in `index.ts` |
| 4 | `tsc` errors on `context` | Tools used the old `execute: async ({ context }) => …` signature | Destructure input directly: `async ({ expression }) => …` |
| 5 | Runtime: *Could not find API key* | Raw `tsx` doesn't load `.env`; gateway reads `process.env` lazily | Add `import 'dotenv/config'` to the runner |

After these, `npx tsx src/run-tool-agent.ts` runs all three prompts and the agent
calls the right tool each time.

## Run

```shell
# Standalone tool-agent runner (calculator / time / fetch-url over 3 prompts)
npx tsx src/run-tool-agent.ts

# Mastra dev server + Studio UI (auto-loads .env)
npm run dev    # → http://localhost:4111
```

Needs `ANTHROPIC_API_KEY` in `week4-mastra/.env`. `npm run dev` loads it
automatically; the standalone runner loads it via `dotenv/config`.

## Architecture

```
src/
├── run-tool-agent.ts            # Standalone runner — dotenv + 3 prompts (today)
└── mastra/
    ├── index.ts                 # Mastra instance — registers agents/tools/workflows/scorers
    ├── agents/
    │   ├── tool-agent.ts        # Tool-using agent: calculator / time / fetch (today)
    │   └── weather-agent.ts     # Bootstrapped example
    ├── tools/
    │   ├── utility-tool.ts      # calculator / current-time / fetch-url tools (today)
    │   └── weather-tool.ts      # Bootstrapped example
    ├── scorers/weather-scorer.ts
    └── workflows/weather-workflow.ts
```

## Conventions (see `AGENTS.md`)

- Load the `mastra` skill before any Mastra work — APIs change between versions; don't rely on cached knowledge.
- Register all agents, tools, workflows, and scorers in `src/mastra/index.ts`.
- Use the `dev` / `build` scripts from `package.json` rather than calling `mastra dev` / `mastra build` directly.

## Getting started (bootstrapped Mastra)

Start the development server:

```shell
npm run dev
```

Open [http://localhost:4111](http://localhost:4111) for [Mastra Studio](https://mastra.ai/docs/studio/overview) — an interactive UI for building and testing agents, plus a local REST API. Edit files in `src/mastra` and the dev server reloads automatically.

## Learn more

To learn more about Mastra, visit the [documentation](https://mastra.ai/docs/) — [agents](https://mastra.ai/docs/agents/overview), [tools](https://mastra.ai/docs/agents/using-tools), [workflows](https://mastra.ai/docs/workflows/overview), [scorers](https://mastra.ai/docs/evals/overview), and [observability](https://mastra.ai/docs/observability/overview).

Part of the IntellAIgent Agent Builder Curriculum, Week 4.
