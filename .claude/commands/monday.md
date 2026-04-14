# /monday — First Rain Weekly Intelligence Briefing
# MESSAGE FORMAT: Full briefing — no character limit. 300-char rule applies to instant alerts only (telegram-alert skill).

Execute the following steps in order. Do not use more than 6 tool calls total.

## STEP 1 — Load Daily Updates (read THIS first — most current data)
Read `_context/daily-updates.md` completely.
Any entry here OVERRIDES stale data in financial-rules.md.
Note all RECEIVED, PAID, STATUS entries from the last 7 days.

## STEP 2 — Load Active Projects and Financials
Read `_context/active-projects.md` completely.
Read `_context/financial-rules.md` for receivables and cash.
Apply Step 1 overrides before composing the briefing.
Do NOT flag items already resolved in daily-updates.md.

## STEP 3 — Check Gmail for Payment Alerts
Search Gmail for emails from the last 7 days containing:
payment, invoice, credited, debited, NEFT, RTGS

Also search Gmail for emails from these clients in the last 7 days:
Secure, TOTO, Elliott, Labguard, Spectrum, Amaara, Klenzaids, Nordex
Payment emails found here also override stale receivables data.

## STEP 4 — Output the Weekly Briefing

Present in this exact format and save to `_outputs/monday-[YYYY-MM-DD].md`:

---
FIRST RAIN — MONDAY BRIEFING
Date: [today's date]
---

🔴 URGENT (action today)
- [List items that cannot wait]

🟠 THIS WEEK (action before Friday)
- [List items due this week]

🟡 WATCH (monitor only)
- [List items to monitor]

💰 RECEIVABLES UPDATE
- [Any payment news from Gmail]
- [Outstanding amounts]

🏗️ PROJECT STATUS
- [Each project: name, days to show, assigned exec]

📋 ONE ACTION PER FLAG
- [Flag] → Action: [next step] → Owner: [name]

---
NOTE: Notion task details not included here.
Type /production for full Notion task breakdown.
---

## STEP 5 — Send Telegram Briefing

Use the `mcp__plugin_telegram_telegram__reply` MCP tool directly:
- chat_id: `8770250893`
- text: the full briefing from Step 4
- format: `text`

Do NOT use a Python script or the Telegram HTTP API. The MCP plugin (`@FirstRainOS1_bot`) is the correct and only channel. If the tool call fails, log to `_outputs/telegram-failed-[date].md` and note in session output.

## STEP 6 — Create Gmail Draft

Create a Gmail draft to niloy@firstrain.co.in using the gmail_create_draft MCP tool with:
- **To:** niloy@firstrain.co.in
- **Subject:** First Rain — Monday Briefing [today's date]
- **Body:** The full briefing text from Step 4

After creating the draft, confirm with: "✅ Gmail draft created — check Drafts in niloy@firstrain.co.in"

If either Step 5 or Step 6 fails, report the error clearly — do not silently skip.