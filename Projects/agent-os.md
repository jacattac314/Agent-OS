---
type: project
aliases: []
status: active
updated: 2026-06-18
sources:
  - Journal/2026-05-28.md
---

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
- [x] Nightly auto-commit cron (`scripts/vault-sync.sh` via launchd at midnight) — live as of 2026-05-28
- [ ] Daily brief population (Asana + GitHub → journal Focus/Tasks)
- [ ] `ASANA_PAT` configured in `scripts/.capture-config` — all auto-captures show "not configured" since 2026-05-29
- [ ] Memory/ seeded with decisions and preferences

## Notes
Daily brief workflow: each morning, read Asana tasks + GitHub activity → write to Journal/{{today}}.md Focus and Tasks sections.
