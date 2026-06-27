---
name: scaffold-day
description: Start a new curriculum day. Given a week and day number as arguments, set up the day's working context — confirm the active project, show recent git state, and prime a notes.md reflection stub. Use at the START of a work session.
---

# Scaffold a new curriculum day

Arguments provided: $ARGUMENTS
(Interpret as "week day", e.g. "5 2" means Week 5, Day 2.)

## Current repo state

Recent commits:
!`git log --oneline -5`

Current branch and status:
!`git status -sb`

## Your tasks

1. Confirm which week's subfolder is active based on the arguments.
2. Check whether that week's notes.md already has a section for this day.
   If not, append a reflection stub with these headers (leave them blank for me to fill):
    - "## What I built"
    - "## What surprised me"
    - "## The realization"
    - "## What I want to remember"
3. Summarize in 2-3 lines: what day this is, what got committed most recently,
   and what the notes stub is ready for. Then stop — I'll take it from here.
