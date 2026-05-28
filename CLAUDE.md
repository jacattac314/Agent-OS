# Agent OS — Vault Context

This vault is the persistent memory layer for Jack's agent setup. Read relevant files here before starting any task.

## Vault Layout
- `Journal/` — daily notes (YYYY-MM-DD.md). Check today's file for active focus and blockers.
- `Projects/` — one file per project. Check before touching related code.
- `Research/` — captured sources, summaries, and links.
- `Tasks/` — active task lists. `inbox.md` is unprocessed capture.
- `Memory/` — long-form context: decisions made, patterns, recurring preferences.
- `Output/` — finished artifacts (drafts, reports, generated files).
- `Templates/` — note templates; do not modify unless asked.

## Workflow
1. Before coding: check `Journal/{{today}}.md` for focus and `Projects/{{relevant}}.md` for context.
2. After completing a task: append a one-line summary to `Journal/{{today}}.md` under "End of Day".
3. New project? Copy `Templates/project.md`, fill Goal and Context, save to `Projects/`.
4. Research worth keeping? Copy `Templates/research.md`, save to `Research/`.

## Writing to the vault
- Use the `vault` MCP filesystem tool to read/write files here.
- Dates in filenames: YYYY-MM-DD format.
- Keep notes short. One idea per file.
