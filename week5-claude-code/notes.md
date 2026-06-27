# Week 5 — Day 1: The extensibility stack + CLAUDE.md + skills

## The mental map (the whole week hangs off this)

- CLAUDE.md: always-true + short, loads every session
- Skills/commands: repeatable playbook, explicit trigger, loads on demand
- Subagents: own context window — for isolation/parallelism (Day 2)
- Hooks: deterministic, can't-trust-the-model enforcement (Day 3)
- MCP: external systems (Day 4)
- Plugins: bundle all the above to share

## What changed since I last built CC tooling

- Slash commands merged into skills (v2.1.101, April 2026). My /review-branch still works.
- Skills are the recommended path; skill wins if it shares a name with a command.
- npm install deprecated; native binary recommended (claude install to migrate).

## What I built

- A CLAUDE.md hierarchy: lean root + scoped week4-mastra/CLAUDE.md (loads on demand)
- ship-day skill: end-of-day ritual (format, lint, README, secret-check, two commits)
- scaffold-day skill: start-of-day priming with $ARGUMENTS + live git state via !`...`

## The realization

The harness IS the moat moving up the stack, in my own workflow. The value isn't
Claude writing code — it's the scaffolding I build so it writes the RIGHT code my
way, every time, without re-explaining.

## What I want to remember

- CLAUDE.md = always-true + short. Skills = sometimes-needed + possibly-long (loads on demand).
- description field drives auto-invocation — write "what AND when"
- !`command` injects live context; $ARGUMENTS parameterizes
- Don't skill-ify one-off tasks. ~30-use threshold is why ship-day/scaffold-day earn it.
