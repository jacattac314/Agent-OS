#!/usr/bin/env python3
"""daily_capture.py — runs at 10pm, writes today's journal from Calendar, Asana, and Git."""

import json
import subprocess
import urllib.request
from datetime import date, datetime
from pathlib import Path

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
    script = """
tell application "Calendar"
    set today to current date
    set bod to today - (time of today)
    set eod to bod + 86399
    set out to ""
    repeat with c in every calendar
        try
            repeat with e in (every event of c whose start date >= bod and start date <= eod)
                set t to time string of (start date of e)
                set out to out & t & " — " & (summary of e) & linefeed
            end repeat
        end try
    end repeat
    return out
end tell"""
    r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    lines = sorted(set(l.strip() for l in r.stdout.strip().splitlines() if l.strip()))
    return "\n".join(f"- {l}" for l in lines) or "(none)"


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
