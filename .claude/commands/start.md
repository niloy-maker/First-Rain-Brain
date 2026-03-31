## Step 0 — Sync live memory from GitHub
Fetch this URL using the WebFetch tool:
https://raw.githubusercontent.com/niloy-maker/First-Rain-Brain/main/MEMORY.md

Use this fetched content as the active MEMORY.md for this session.
Ignore the local MEMORY.md — treat it as potentially stale.
If the fetch fails, fall back to the local MEMORY.md and warn:
"⚠️ GitHub sync failed — reading from local file. May be stale."

## Step 1 — Summarise
From the fetched memory, summarise in 5 bullets:
1. 🔴 Active alerts
2. 🔴 Receivables — top 3 by amount
3. 🟠 Active projects — show date + days remaining
4. 🟠 Open quote decisions
5. 📝 Last session — date + key decisions made

Then say: "Memory loaded from GitHub. What are we working on today?"