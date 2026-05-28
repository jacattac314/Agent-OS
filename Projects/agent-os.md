# Agent OS

## Goal
A persistent memory and task layer that makes Claude useful across sessions — vault as the source of truth, MCP as the bridge.

## Context
- Repo: https://github.com/jacattac314/Agent-OS
- Vault: ~/obsidian-agentic-vault (MCP server: "vault")
- Claude Code registered vault via `claude mcp add vault --scope user`

## Architecture
- `Journal/` — daily focus + end-of-day log
- `Projects/` — one file per active project (this file is the example)
- `Tasks/inbox.md` — unprocessed captures, triaged into journal
- `Memory/` — long-form decisions, preferences, recurring patterns
- `Research/` — captured sources and summaries
- `Output/` — generated artifacts

## Status
- [x] Vault created and structured
- [x] MCP server registered (vault, user scope)
- [x] Committed to GitHub
- [x] .gitignore added
- [ ] Daily auto-commit cron
- [ ] Daily brief population (Asana + GitHub → journal Focus/Tasks)
- [ ] Memory/ seeded with decisions and preferences

## Notes
Daily brief workflow: each morning, read Asana tasks + GitHub activity → write to Journal/{{today}}.md Focus and Tasks sections.
