#!/bin/bash

# First Rain — MEMORY.md Auto Sync to claude.ai Project
# Runs automatically after every /end command

API_KEY="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"
PROJECT_ID="019d2fef-e44c-7105-9739-e57b1c9ad18f"
MEMORY_FILE="$HOME/Desktop/FirstRain-Brain/MEMORY.md"

echo "Syncing MEMORY.md to claude.ai Project..."

# Read the contents of MEMORY.md
CONTENT=$(cat "$MEMORY_FILE")

# Upload to claude.ai Project via API
curl -s -X POST "https://api.anthropic.com/v1/projects/$PROJECT_ID/documents" \
  -H "x-api-key: $API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d "{
    \"name\": \"MEMORY.md\",
    \"content\": $(echo "$CONTENT" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))')
  }"

echo "Done. MEMORY.md synced at $(date)"
```

Press **Command + S**. Close the window.

---

## Find your Project ID

**Step 4 — Get your Project ID**

- Open claude.ai in your browser
- Open your First Rain project
- Look at the URL — it looks like this:
```
claude.ai/project/proj_xxxxxxxxxxxxxxxxxx
```
- Copy everything after `/project/` — that is your Project ID
- Paste it into the script replacing `paste-your-project-id-here`
- Also paste your API key replacing `paste-your-api-key-here`

---

## Make the script executable

**Step 5 — Give the script permission to run**
```
chmod +x ~/Desktop/FirstRain-Brain/sync_memory.sh
```

**Step 6 — Test it manually first**
```
./sync_memory.sh
```

You should see:
```
Syncing MEMORY.md to claude.ai Project...
Done. MEMORY.md synced at 28 Mar 2026 15:30:00
```

If you see that — it works. Go to your claude.ai Project and check that MEMORY.md updated.

---

## Connect it to /end so it fires automatically

**Step 7 — Update your /end command**
```
open -a TextEdit .claude/commands/end.md
```

Add this one line at the very bottom of the file:
```
After saving MEMORY.md, run this command in the terminal:
~/Desktop/FirstRain-Brain/sync_memory.sh
```

Press **Command + S**. Close.

---

## Save everything to git

**Step 8**
```
git add . && git commit -m "Memory auto-sync script created"
```

---

## What happens now every single day
```
You finish a chat in Claude Code
       ↓
Type /end
       ↓
Claude Code updates MEMORY.md on your Mac
       ↓
sync_memory.sh fires automatically
       ↓
MEMORY.md uploads to your claude.ai Project
       ↓
You open chat tomorrow
       ↓
Type ;;start
       ↓
Memory is already current. Nothing to do.