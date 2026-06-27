---
name: ship-day
description: Run the end-of-day curriculum ritual — format, lint, update README status, verify no secrets staged, and prepare the two standard commits. Use at the end of a work session when the day's code is done.
---

# Ship the day's work

Follow these steps in order. Stop and ask me if anything looks wrong.

## 1. Format and lint
For a Python week, run from the active week's directory:
- `uv run ruff format`
- `uv run ruff check --fix`
For the TypeScript (Mastra) week, run the project's lint/format script if one exists; otherwise rely on tsc.

## 2. Update the README Status
Open the active week's README.md. Find the Status or Day-tracking section and
mark today's day complete, matching the existing format. Don't invent a format —
mirror what's already there.

## 3. Safety check before staging
Run `git status` and confirm NONE of these are staged or untracked-and-about-to-be-added:
- .env  (any .env file)
- .chroma/
- *.db
- node_modules/
- .mastra/
If any appear, STOP and tell me — do not proceed.

## 4. Prepare the commits
Ask me for the day's theme in one short phrase if I haven't given it.
Then stage the code and propose TWO commits, in this order:
- `git commit -m "Week X Day Y: <theme>"`  (the day's work)
- `git commit -m "Day Y reflections"`  (the notes.md update)
Show me the exact commands. Do NOT run the commits until I confirm.

## 5. Confirm
Print a one-line summary: what was committed, what was skipped, anything I should review.