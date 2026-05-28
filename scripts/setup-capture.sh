#!/bin/bash
# setup-capture.sh — one-time setup for daily_capture.py

set -euo pipefail

CONFIG="/Users/jack/obsidian-agentic-vault/scripts/.capture-config"
PLIST="/Users/jack/Library/LaunchAgents/com.justjack.vault-capture.plist"

echo ""
echo "=== Daily Capture Setup ==="
echo ""

# Google Calendar ICS URL
echo "--- Google Calendar ---"
echo "1. Open https://calendar.google.com → Settings (gear) → your calendar → scroll to"
echo "   'Secret address in iCal format' → copy the URL"
echo "Leave blank to skip:"
read -r GOOGLE_CALENDAR_ICS_URL
echo ""

# Asana PAT
echo "--- Asana ---"
echo "Get your PAT at: https://app.asana.com/0/my-apps → Create token"
echo "Leave blank to skip:"
read -r -s ASANA_PAT
echo ""

cat > "$CONFIG" <<EOF
GOOGLE_CALENDAR_ICS_URL=${GOOGLE_CALENDAR_ICS_URL}
ASANA_PAT=${ASANA_PAT}
EOF
chmod 600 "$CONFIG"
echo "Config saved to $CONFIG (gitignored)"

# Load launchd
if launchctl list | grep -q "com.justjack.vault-capture"; then
    launchctl unload "$PLIST" 2>/dev/null || true
fi
launchctl load "$PLIST"
echo "LaunchAgent loaded — will run daily at 10pm"

echo ""
echo "Run a test now? (y/n)"
read -r yn
if [[ "$yn" == "y" ]]; then
    python3 /Users/jack/obsidian-agentic-vault/scripts/daily_capture.py
fi
