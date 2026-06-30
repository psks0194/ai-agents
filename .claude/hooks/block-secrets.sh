#!/usr/bin/env bash
# PreToolUse guard: block Claude from reading/editing/writing secret files.
# Receives event JSON on stdin. Exit 2 = block the tool call.

INPUT=$(cat)
FILE=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

# No file_path (e.g. a Bash call) — scan the command string instead so the
# guard can't be bypassed by reading secrets via cat/grep/cut/env/etc.
if [ -z "$FILE" ]; then
  CMD=$(echo "$INPUT" | jq -r '.tool_input.command // empty')
  [ -z "$CMD" ] && exit 0
  # Match a real env file referenced anywhere in the command, but allow
  # .env.example/.sample/.template.
  if echo "$CMD" | grep -qE '\.env([^[:alnum:]_.]|$)' \
     || echo "$CMD" | grep -qE '\.env\.(local|prod|production|dev|development|staging|test)'; then
    echo "BLOCKED: command references a secret .env file. Denied." >&2
    exit 2
  fi
  if echo "$CMD" | grep -qE '(id_rsa|\.pem([^[:alnum:]]|$)|credentials|secrets\.ya?ml)'; then
    echo "BLOCKED: command references a secret/credential file. Denied." >&2
    exit 2
  fi
  exit 0
fi

BASENAME=$(basename "$FILE")

# Explicitly ALLOW example/template env files — they're safe and useful.
case "$BASENAME" in
  .env.example|.env.sample|.env.template) exit 0 ;;
esac

# BLOCK real env files (.env, .env.local, .env.production, etc.)
case "$BASENAME" in
  .env|.env.*)
    echo "BLOCKED: $FILE is a secret file. Claude must not read, edit, or write it." >&2
    exit 2
    ;;
esac

# BLOCK other common secret artifacts.
if echo "$BASENAME" | grep -qE '(id_rsa|\.pem$|credentials|secrets\.ya?ml)'; then
  echo "BLOCKED: $FILE looks like a secret/credential file. Denied." >&2
  exit 2
fi

exit 0