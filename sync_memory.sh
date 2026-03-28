#!/bin/bash

# First Rain — MEMORY.md Auto Sync
# Commits MEMORY.md to git so it stays versioned
# Run manually or after /end

REPO="$HOME/Desktop/FirstRain-Brain"
MEMORY_FILE="$REPO/MEMORY.md"

echo "Syncing MEMORY.md via git..."

cd "$REPO" || { echo "Error: repo not found at $REPO"; exit 1; }

git add MEMORY.md

if git diff --cached --quiet; then
  echo "No changes to sync."
  exit 0
fi

git commit -m "Auto-sync: MEMORY.md updated $(date '+%d %b %Y %H:%M')"

echo "Done. MEMORY.md committed at $(date)"
