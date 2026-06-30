#!/usr/bin/env bash
# PostToolUse: auto-format the file Claude just edited or wrote.
# PostToolUse exit code does not block (the edit already happened),
# so we always exit 0; formatting is best-effort and idempotent.

INPUT=$(cat)
FILE=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

# Nothing to format if there's no path or the file doesn't exist.
{ [ -z "$FILE" ] || [ ! -f "$FILE" ]; } && exit 0

case "$FILE" in
  *.py)
    # uvx runs ruff in an ephemeral env — no per-project install needed.
    if command -v uvx >/dev/null 2>&1; then
      uvx ruff format "$FILE" >/dev/null 2>&1
      uvx ruff check --fix "$FILE" >/dev/null 2>&1
    fi
    ;;
  *.ts|*.tsx|*.js|*.jsx|*.json)
    if command -v npx >/dev/null 2>&1; then
      npx --no-install prettier --write "$FILE" >/dev/null 2>&1
    fi
    ;;
esac

exit 0