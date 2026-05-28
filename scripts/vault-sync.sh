#!/bin/bash
set -euo pipefail

VAULT="/Users/jack/obsidian-agentic-vault"
DATE=$(date +%Y-%m-%d)
LOG="$VAULT/scripts/vault-sync.log"

cd "$VAULT"

if [[ -z "$(git status --porcelain)" ]]; then
  echo "[$DATE] No changes — skipping commit" >> "$LOG"
  exit 0
fi

git add -A
git commit -m "Daily vault sync — $DATE"
git push origin main >> "$LOG" 2>&1
echo "[$DATE] Synced successfully" >> "$LOG"
