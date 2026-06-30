#!/usr/bin/env bash
# PreToolUse guard on Bash: block a small set of genuinely destructive commands.
# Exit 2 = deny. Keep this conservative to avoid false positives.

INPUT=$(cat)
CMD=$(echo "$INPUT" | jq -r '.tool_input.command // empty')
[ -z "$CMD" ] && exit 0

# rm -rf on a root, home, or $HOME path
if echo "$CMD" | grep -qE 'rm[[:space:]]+-[a-zA-Z]*r[a-zA-Z]*f?[[:space:]]+(/|~|\$HOME)'; then
  echo "BLOCKED: refusing 'rm -rf' on a root/home path. If intended, run it yourself." >&2
  exit 2
fi

# Force push
if echo "$CMD" | grep -qE 'git[[:space:]]+push[[:space:]].*(--force|-f)([[:space:]]|$)'; then
  echo "BLOCKED: refusing a force push. Push without --force, or do it manually if you mean it." >&2
  exit 2
fi

# Overwriting .env via shell redirect (complements the file-tool secret block)
if echo "$CMD" | grep -qE '>[[:space:]]*\.env([[:space:]]|$)'; then
  echo "BLOCKED: refusing to overwrite .env via shell redirect." >&2
  exit 2
fi

exit 0