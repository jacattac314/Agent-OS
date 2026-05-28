#!/usr/bin/env python3
"""daily_capture.py — runs at 10pm, writes today's journal from Calendar, Asana, and Git."""

import json
import subprocess
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path
import sys

VAULT = Path.home() / "obsidian-agentic-vault"
TODAY = date.today().isoformat()
JOURNAL = VAULT / "Journal" / f"{TODAY}.md"
CONFIG = VAULT / "scripts" / ".capture-config"
MARKER = "<!-- auto-captured -->"


def git_commits():
    r = subprocess.run(
        ["git", "-C", str(VAULT), "log", f"--since={TODAY}T00:00:00", "--format=- %h %s"],
        capture_output=True, text=True,
    )
    return r.stdout.strip() or "(none)"


def calendar_events():
    # Try Claude-written cache first (written during morning session via MCP)
    cache = VAULT / "scripts" / ".calendar-cache" / f"{TODAY}.json"
    if cache.exists():
        import json as _json
        events = _json.loads(cache.read_text())
        return "\n".join(f"- {e['time']} — {e['summary']}" for e in events)

    # Fallback: ICS URL if configured
    ics_url = load_pat("GOOGLE_CALENDAR_ICS_URL")
    if not ics_url:
        return "(no calendar cache — open Claude Code to populate)"
    try:
        from icalendar import Calendar
        import urllib.request as req_mod
        with req_mod.urlopen(ics_url, timeout=15) as r:
            cal = Calendar.from_ical(r.read())
        today = date.today()
        events = []
        for component in cal.walk():
            if component.name != "VEVENT":
                continue
            dtstart = component.get("DTSTART")
            if dtstart is None:
                continue
            val = dtstart.dt
            if isinstance(val, datetime):
                event_date = val.astimezone().date()
                time_str = val.astimezone().strftime("%-I:%M %p")
            else:
                event_date = val
                time_str = "all-day"
            if event_date != today:
                continue
            summary = str(component.get("SUMMARY", "(no title)"))
            events.append((time_str, summary))
        events.sort()
        return "\n".join(f"- {t} — {s}" for t, s in events) or "(no events today)"
    except Exception as e:
        return f"(calendar error: {e})"


def load_pat(key):
    if not CONFIG.exists():
        return None
    for line in CONFIG.read_text().splitlines():
        if line.startswith(f"{key}="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def asana_tasks():
    pat = load_pat("ASANA_PAT")
    if not pat:
        return "(not configured — add ASANA_PAT to scripts/.capture-config)"
    try:
        req = urllib.request.Request(
            "https://app.asana.com/api/1.0/tasks/me?completed_since=now&opt_fields=name,due_on",
            headers={"Authorization": f"Bearer {pat}"},
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            tasks = json.loads(r.read()).get("data", [])
        return "\n".join(f"- [ ] {t['name']}" for t in tasks[:25]) or "(none)"
    except Exception as e:
        return f"(error: {e})"


def main():
    if JOURNAL.exists() and MARKER in JOURNAL.read_text():
        print(f"[{datetime.now()}] Already captured {TODAY} — skipping")
        return

    cal = calendar_events()
    git = git_commits()
    tasks = asana_tasks()

    if not JOURNAL.exists():
        template = (VAULT / "Templates" / "daily-note.md").read_text()
        JOURNAL.write_text(template.replace("{{date}}", TODAY))

    existing = JOURNAL.read_text().rstrip()

    block = f"""

---
{MARKER}
## Auto-Capture — {datetime.now().strftime("%I:%M %p")}

### Calendar
{cal}

### Commits
{git}

### Open Tasks
{tasks}
"""
    JOURNAL.write_text(existing + "\n" + block)
    print(f"[{datetime.now()}] Written → {JOURNAL}")


if __name__ == "__main__":
    main()
