# Daily Capture

## Goal
Auto-populate today's journal at end of day by pulling from all connected services — no manual logging required.

## Sources
| Source | What it captures |
|---|---|
| Google Calendar | Scheduled blocks, meetings, events |
| Asana | Tasks completed, overdue, in-progress |
| Gmail | Applications sent, recruiter replies, key inbound threads |
| Git (Agent-OS) | Commits made across the day |
| Slack | Active channels, messages sent (via Hermes) |
| LinkedIn (via Gmail) | Job alerts matched, applications confirmed |

## Architecture
- **Trigger:** Local launchd job at 10pm CT (before midnight sync commits)
- **Script:** `scripts/daily-capture.sh` — calls Claude Code with vault MCP + Gmail/Calendar/Asana MCPs
- **Output:** Writes to `Journal/YYYY-MM-DD.md` under Focus, Dev, Career, Notes, End of Day
- **Commit:** Midnight `vault-sync.sh` picks it up and pushes to GitHub

## Why local (not remote CCR)
Remote agents can clone the repo but can't see local Obsidian edits made that day. Local script has access to everything — vault edits + all MCP connections authenticated as you.

## Status
- [x] Data sources identified and tested (Calendar, Asana, Gmail, Git)
- [x] Example output written — see Journal/2026-05-28.md
- [ ] `scripts/daily-capture.sh` — shell script that invokes Claude via MCP
- [ ] LaunchAgent plist at 10pm CT
- [ ] Slack pull (needs channel IDs mapped)

## Notes
- Gmail: filter `-category:promotions -category:social` to cut noise
- Asana: `completed_since: today` for done tasks; omit for in-progress
- Calendar: pull `startTime: today 00:00`, `endTime: today 23:59`
- Git: `git log --since=midnight --format="%h %s"` across all local repos
