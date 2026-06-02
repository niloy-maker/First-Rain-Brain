---
name: context
version: "1.0"
description: Load First Rain context at the start of every session. Run when session starts, or when asked for a briefing, status update, or morning summary.
---

# Context Loader — First Rain V2

## Steps (in order)
1. Read CLAUDE.md
2. Read _context/active-projects.md
3. Read _context/decision-log.md
4. Read _context/session-log.md (last 3 entries only)
5. Notion connectivity probe — fetch the FR Production Tracker via the DURABLE CONNECTOR (primary):
   - Call `mcp__4f0ff3f0-60f2-4485-9022-56005bb68c69__notion-fetch` (load via ToolSearch) with id: ac84c676ad7249d2a79732d842f71d62
   - If it succeeds: note "Notion ✓" in the output line below. (Do NOT report DISCONNECTED just because the `plugin:Notion:notion` OAuth endpoint is unauthenticated — that endpoint expires constantly and is only an optional fallback. The connector is what matters.)
   - If the connector fails: retry once with the fallback `mcp__plugin_Notion_notion__notion-fetch` (same id).
   - Only if BOTH fail: say "⚠️ NOTION DISCONNECTED — re-authorize at app.notion.com/install-integration (select Team First Rain workspace). Production tracker data may be stale." and note the last-pulled date from active-projects.md.

## Output — say exactly this
"First Rain V2 loaded.
[N] active projects. Last session: [date from session-log].
Top priority: [#1 urgent item from active-projects.md].
Active alerts: [any margin, concentration, or runway flags].
Notion: [✓ connected / ⚠️ DISCONNECTED — re-authorize now]
What are we working on?"

## Never skip the alerts line
If operating cash below ₹76.5L — say RUNWAY ALERT.
If Secure Meters above 25% of pipeline — say CONCENTRATION ALERT.
If any active project under 7 days to show — say URGENT: [project name].
If Notion probe fails — say NOTION DISCONNECTED (production tracker data stale since [date]).
