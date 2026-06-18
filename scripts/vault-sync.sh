#!/bin/bash
set -euo pipefail

VAULT="/Users/jack/obsidian-agentic-vault"
DATE=$(date +%Y-%m-%d)
LOG="$VAULT/System/logs/vault-sync.log"

cd "$VAULT"
mkdir -p "$(dirname "$LOG")"

if [[ -z "$(git status --porcelain)" ]]; then
  UPSTREAM=$(git rev-parse --abbrev-ref --symbolic-full-name @{u} 2>/dev/null || true)
  if [[ -n "$UPSTREAM" && -n "$(git log --oneline "$UPSTREAM"..HEAD 2>/dev/null)" ]]; then
    git push origin main >> "$LOG" 2>&1
    echo "[$DATE] Pushed pending commits" >> "$LOG"
    exit 0
  fi
  echo "[$DATE] No changes — skipping commit" >> "$LOG"
  exit 0
fi

git add -A
git commit -m "Daily vault sync — $DATE"
git push origin main >> "$LOG" 2>&1
echo "[$DATE] Synced successfully" >> "$LOG"
