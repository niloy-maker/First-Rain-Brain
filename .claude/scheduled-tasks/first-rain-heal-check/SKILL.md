---
name: first-rain-heal-check
description: DISABLED in-app — now driven authoritatively by launchd com.firstrain.sched-first-rain-heal-check (10:05, headless, session-independent). SKILL.md still the source of truth. Re-enable only if reverting to in-app scheduling.
---

You are running the First Rain post-briefing self-healing check. Pure verification + safe remediation — do NOT regenerate the briefing itself. The morning's `first-rain-monday-sync` task fired at ~09:08 IST; you start ~10:05 IST, after the morning sync has had time to complete.

Working directory: /Users/monicadebnath/Desktop/Andrej_Karpathy_Obsidian_FirstRain_Brain

**TELEGRAM RULE — always send at Step 6, no exceptions:**
Always send a Telegram after completing all checks. Niloy expects a confirmation that the heal check ran. Use this format:
- All green → `🩺 Heal check · <date> · ✅ All systems green` (single line, no extra detail needed)
- Auto-healed items → `🩺 Heal check · <date>\n⚠️ Healed:\n- <action> ✅\n…`
- Unresolved failures → `🩺 Heal check · <date>\n🔴 Unresolved — action needed:\n- <issue>\n…`
Never skip Step 6.

## PRE-FLIGHT — Load deferred tools (ONE batched call)
Load every required tool in a SINGLE ToolSearch call:

ToolSearch: "select:mcp__plugin_telegram_telegram__reply,mcp__google-drive__download_file_content,mcp__scheduled-tasks__list_scheduled_tasks,mcp__gmail__create_draft,mcp__gmail__list_labels,mcp__dfb7f7c2-658a-476e-986c-8a792b7b8462__Bigin_getOrganizationDetails,mcp__plugin_Notion_notion__notion-fetch,mcp__4f0ff3f0-60f2-4485-9022-56005bb68c69__notion-fetch,mcp__a9a30244-5e56-4840-804f-19f9622e0bf6__get_file_metadata,mcp__plugin_mongodb_mongodb__connect,mcp__plugin_mongodb_mongodb__find"

`create_draft` and `list_labels` are loaded for the Gmail fallback path in STEP 6. Bigin, Notion, Drive, and MongoDB/FRBIS tools are loaded for STEP 5B connection health checks.

Do not proceed until loaded.

## STEP 0 — Authoritative date
Run `date "+%Y-%m-%d %A %d %B %Y" < /dev/null` and use both forms. Today's filename is `_outputs/briefing-YYYY-MM-DD.md`. Do NOT pull date from CLAUDE.md memory.

## STEP 0B — Morning sync in-progress guard
Before any checks, call `mcp__scheduled-tasks__list_scheduled_tasks` and find `first-rain-monday-sync`. Compare its `lastRunAt` date against today's date from STEP 0.

**Case A — `lastRunAt` is from a PREVIOUS day (morning sync has not run today yet):**
The heal check fired before the morning sync started (catch-up scenario). Log "⏳ Morning sync not yet run today — heal check skipping all verifications." Append a brief note to `_outputs/briefing-YYYY-MM-DD.md` if it exists, otherwise write nothing. Do NOT send Telegram. Go directly to STEP 7.

**Case B — `lastRunAt` is today AND within the last 60 minutes:**
Ambiguous: the morning sync may be (a) legitimately mid-run, OR (b) it fired at the same time as this heal-check as a catch-up after the Mac slept, and died on launch (the 23-May-2026 pattern — the daemon stamped `lastRunAt` but the agent made zero tool calls and wrote no files). The old logic assumed (a) and silently skipped, so a dead sync produced no briefing AND no alert. Do NOT assume — verify the briefing FILE.

Decision tree (the morning sync writes `_outputs/briefing-YYYY-MM-DD.md` in its STEP 4, after the slow Notion/Gmail failsafe gates — so a healthy run may not have written it for several minutes):

1. If `_outputs/briefing-YYYY-MM-DD.md` EXISTS and its step log shows `Telegram: ✅` → sync finished. Proceed normally through all steps.
2. If it EXISTS but the step log shows `Telegram: pending` → genuinely in progress (sync is in the long STEP 5 finance pipeline). Log "⏳ Morning sync in progress — skipping Telegram/Gmail step log checks" and jump to STEP 2 (skip STEP 1 log check). Do NOT flag missing Telegram/Gmail as a failure.
3. If it does NOT exist → poll before concluding. A live sync writes the briefing within ~10 min of starting; a dead sync never will:
   ```
   cd ~/Desktop/Andrej_Karpathy_Obsidian_FirstRain_Brain
   F="_outputs/briefing-$(date +%F).md"
   for i in $(seq 1 10); do [ -f "$F" ] && { echo "appeared after ${i}min"; break; }; sleep 60; done
   [ -f "$F" ] && echo "BRIEFING_NOW_EXISTS" || echo "BRIEFING_STILL_MISSING"
   ```
   - If `BRIEFING_NOW_EXISTS` → the sync was just slow; re-evaluate from step 1/2 above.
   - If `BRIEFING_STILL_MISSING` after the 10-min poll → the morning sync died on launch. Send this Telegram to chat_id `"8770250893"` and STOP (do not regenerate, do not run STEP 2+):
     `🔴 Heal check · <date> — morning sync FAILED. first-rain-monday-sync stamped lastRunAt <HH:MM IST> but produced no briefing in 10+ min (likely catch-up-after-sleep death). No 9 AM Telegram/Gmail went out. Run /monday manually to recover.`

     **This alert is MANDATORY and must always be delivered.** If `mcp__plugin_telegram_telegram__reply` fails or errors, immediately fall back to a Gmail draft (the STEP 6 Gmail-fallback path) carrying the same content — a dead morning-sync launch must NEVER result in silence. Log which channel delivered. (The 1 PM midday refresh is the delivery backstop: it detects the missing briefing and auto-runs full recovery via the orchestrator.)

**Case C — `lastRunAt` is today AND more than 60 minutes ago:**
Morning sync is done. Proceed normally through all steps.

## STEP 1 — Briefing existence + freshness

**A — Today's briefing:**
Check `_outputs/briefing-YYYY-MM-DD.md`:
- exists? size > 1KB?
- header `Date: <weekday>, DD Month YYYY` matches today's `date` output exactly?
- step completion log contains `Telegram: ✅`?
- step completion log contains `Gmail draft: ✅`?

If the briefing does NOT exist: send Telegram alert to chat_id `"8770250893"` saying the morning sync didn't produce output and stop. Don't try to regenerate.

If the date in the header doesn't match today's `date` output: this matches the 4-May-2026 incident pattern. Send Telegram with both dates and prepend a `🚨 DATE MISMATCH — see correction below` line to the briefing file (overwrite, don't delete — per CLAUDE.md prohibited actions).

If `Telegram: ✅` is absent from the step completion log (but briefing file exists): the morning sync wrote the briefing but crashed or stalled before Step 8. Add to 🔴 failure list: "Briefing written but no Telegram sent — Step 8 failed or never ran." This will trigger a STEP 6 alert.

If `Gmail draft: ✅` is absent from the step completion log (but briefing file exists and Telegram was sent): Step 9 failed. Add to ⚠️ issue list: "Briefing and Telegram OK, but Gmail draft not created — Step 9 failed." This will trigger a STEP 6 alert.

**B — Yesterday's EOD check (P2.9):**
Compute yesterday's date and check `_outputs/briefing-[YESTERDAY].md`:
- If file does not exist: skip (yesterday's morning sync may have failed — out of scope for today's heal-check).
- If file exists: search for a line matching `- EOD refresh [HH:MM IST]:` in the Step Completion Log.
  - If the line is present and contains `Telegram sent`: yesterday's EOD completed normally. No action.
  - If the line is present but does NOT contain `Telegram sent`: add to today's Telegram summary note: "⚠️ Yesterday's EOD refresh logged but Telegram was not confirmed sent — verify manually."
  - If the line is absent entirely: add to today's Telegram summary note: "⚠️ Yesterday's EOD refresh produced no log entry — Telegram status unknown."

## STEP 2 — Finance pipeline output freshness
Check these files exist with mtime within the last 6 hours:
- `data/projects/bigin_pipeline_classified.json`
- `data/projects/sheet_cash_position.json` `sheet_treasury.json` `sheet_receivables.json` `sheet_payables.json` `sheet_statutory.json` `sheet_notes.json` `sheet_projects.json`
- `data/projects/sheet_bank_transactions.json`
- `data/projects/momentum.json` `data/projects/drift_report.json` `data/projects/cashflow.json`
- `dashboards/dashboard.html`

For any missing/stale file, attempt one safe remediation pass — re-run the relevant Python script from the vault root:
- `sheet_*.json` missing → `python3 scripts/projects/read_cashflow_xlsx.py` (needs cached xlsx; if cache also stale, fetch via Drive MCP `download_file_content` for fileId `1kBYFQfER46gAqcnCA2jaGkjG_h4iEHj4c6EDVVvREKA` and decode inline).
- momentum/drift/cashflow stale → `python3 scripts/projects/compute_momentum.py` and `python3 scripts/projects/drift_check.py` then `python3 scripts/projects/build_cashflow_json.py --from-files`.
- dashboard.html stale → `python3 scripts/projects/build_cashflow_json.py --from-files`.

Track which files were healed (auto-fix list) and which could not be fixed (failure list).

## STEP 3 — Dashboard + bank validation
Run this validator inline:
```
cd ~/Desktop/Andrej_Karpathy_Obsidian_FirstRain_Brain && python3 -c "
import json, re
issues=[]
html=open('dashboards/dashboard.html').read()
if '{{CASHFLOW_JSON}}' in html: issues.append('placeholder unsubstituted in dashboard.html')
n=html.count('NaN')
if n>0: issues.append(f'NaN appears {n}x in dashboard.html')
u=len(re.findall(r'\bundefined\b', html))
if u>0: issues.append(f'undefined token {u}x in dashboard.html')
bt=json.load(open('data/projects/sheet_bank_transactions.json'))
unp=bt.get('meta',{}).get('unparseableCount',0)
if unp>0:
  warns=bt.get('meta',{}).get('warnings',[])[:3]
  issues.append(f'HDFC unparseable={unp} (regex stale). Samples: {warns}')
cp=json.load(open('data/projects/sheet_cash_position.json'))
op=cp.get('cash',{}).get('operatingCash',0)
if op<7650000: issues.append(f'operatingCash Rs {op:,.0f} < Rs 76.5L floor')
dr=json.load(open('data/projects/drift_report.json'))
ac=dr.get('counts',{}).get('ALERT',0)
if ac>0: issues.append(f'drift_report has {ac} ALERT(s)')
print(json.dumps(issues))
"
```

**Also read `data/projects/pipeline_health.json`** (written by the orchestrator `run_pipeline.py` on the morning run):
- If missing, or its `generated_at` date is not today → add 🔴 "pipeline_health.json missing/stale — orchestrator may not have run this morning."
- If `overall` == `failed` → add each `failed` source (name + `detail`) to the 🔴 unresolved list.
- If `overall` == `degraded` → add each `stale` source (name + `detail`) to the ⚠️ note list (informational — a stale source means the briefing ran on last-good cached data, not a hard failure).

## STEP 4 — Cloudflare deploy freshness
First read `data/projects/deploy_status.json` — the 9:08 sync's authoritative deploy outcome.
- If `"result":"OK"` AND `checked_at_utc` is from today → deploy is fresh, nothing to do.
- Otherwise (FAIL/WARN, missing, or stale timestamp) → re-publish via the single canonical script (this is the self-heal):
```
cd ~/Desktop/Andrej_Karpathy_Obsidian_FirstRain_Brain && bash scripts/deploy_dashboard.sh && cat data/projects/deploy_status.json
```
The script sources the token, repairs PATH, and refuses to publish a broken dashboard — so this self-heal actually works headlessly (the previous inline `wrangler` copy here was missing `source .secrets/cloudflare.env`, so it failed identically to the sync and could never heal anything). If the re-publish still returns `"result":"FAIL"`, add it to the failure list with the exact `reason`/`detail` — that means the token is revoked or wrangler is broken (needs Niloy), not a transient miss. Do NOT inline a raw `wrangler pages deploy`.

## STEP 4B — HDFC pipeline integrity (prevents silent balance drift)

Run two cheap Gmail probes that catch the failure modes responsible for
today's ₹23L silent overshoot:

1. **Unlabeled-txn drift:**
   Call `mcp__gmail__search_threads` with
   `query: from:alerts@hdfcbank.bank.in -label:finance-hdfc-txn newer_than:7d`,
   `pageSize: 10`. Expected `resultCountEstimate = 0`. Anything > 0 means
   HDFC introduced a new subject template that the Gmail filter doesn't
   route, so the daily morning sync (which keys on the label) will lose
   those txns silently. Add to ⚠️ issue list: "HDFC filter gap — [N]
   alerts unlabeled in last 7d; oldest subject: '<subject>'". The morning
   sync's sender-only query covers this; the filter is just for human
   browsability, but a growing gap predicts a parser-side regression too.

2. **Balance reconciliation gate:**
   Read `data/projects/cashflow.json` → `FR.bankReconcile`. Expected
   `status: "ok"` or `"no_embedded"` (the latter is benign — just means
   the morning sync didn't fetch FULL_CONTENT). If `status == "drift"`,
   add to ⚠️ issue list with the `note`. If `status == "material_gap"`
   (Δ > ₹1L), add to 🔴 failure list: "HDFC balance drift Δ [delta_inr]
   — refetch hdfc cache before next deploy". This is the guard that
   would have caught today's 16-Jun ₹23L overshoot.

## STEP 4C — Execution-coverage data health (prevents silent by-project-month blackout)

Read `data/projects/cashflow.json` → `FR.pipelineCoverageMeta`. Two gates:

1. **`dataAvailable == false`** — the by-project-month coverage strip on the
   dashboard is blank. This is a P0 signal: either the Bigin COQL query is
   silently falling back to `NO_PROJECT_MONTH` (Bigin schema drift), or the
   fetcher was replaced with an older version that never asked for the field.
   Add to 🔴 failure list: "Exec-coverage strip blank —
   FR.pipelineCoverageMeta.dataAvailable=false. Bigin fetcher regressed or
   Project_Month column removed. Blocks tomorrow's morning briefing coverage
   alerts."

2. **`missingExecMonthCount` climbed sharply** — read yesterday's cashflow.json
   from `_outputs/cashflow-snapshots/YYYY-MM-DD.json` if the morning sync saves
   one, or fall back to just checking the absolute count. If today's count > 60
   (roughly 40% of the 155-deal pipeline), add to ⚠️ issue list: "Project_Month
   tagging gap widening ([N] deals untagged) — Chinmay/Niloy to tag before next
   week's briefings mis-project the load." (The current baseline on 07-Jul-2026
   is ~101 untagged; 60 was chosen as the "getting better" threshold, not a
   ceiling.)

Related: `Bigin_getRecordsUsingCoqlQuery` schema — **the SELECT lives in
`~/.claude/scheduled-tasks/first-rain-monday-sync/SKILL.md` Step 5A**, NOT
in `scripts/projects/fetch_bigin_pipeline.py` (which requires .env creds
and is unused by the SKILL — noted 2026-07-07). If future edits drop
`Project_Month` from the SKILL COQL, this alert is the only guard. When
adding fields to Bigin fetches, always update BOTH the SKILL SELECT AND
the Python transform block that shapes the response into raw.json.

Grep-canary: heal-check should also `grep -q 'Project_Month' ~/.claude/scheduled-tasks/first-rain-monday-sync/SKILL.md` — if that fails, add to 🔴 failure list "SKILL COQL regressed — Project_Month dropped from morning-sync SKILL Step 5A".

## STEP 5 — Schedule sanity
Use `mcp__scheduled-tasks__list_scheduled_tasks` to confirm `first-rain-monday-sync` is enabled and `lastRunAt` is within the last 90 minutes. If `lastRunAt` is stale or `enabled=false`, add to failure list (P0).

## STEP 5B — MCP connection health (prevents silent disconnection overnight)

Test Bigin and Notion with lightweight calls. A disconnected MCP means tomorrow's 9 AM sync falls back to stale cached data — catching it now gives Niloy time to re-auth before the next run.

**Bigin:**
Call `mcp__dfb7f7c2-658a-476e-986c-8a792b7b8462__Bigin_getOrganizationDetails` (no params).
- Returns org data → ✅ Bigin live. Note in audit trail.
- Returns auth error, timeout, or tool-not-found → 🔴 add to unresolved list: "Bigin MCP (`mcp__dfb7f7c2-...`) disconnected — morning sync will fall back to cached pipeline. Re-auth: open Claude Code in the vault and run `mcp__bigin__authenticate`."

**Notion:** PRIMARY is the durable connector `mcp__4f0ff3f0-60f2-4485-9022-56005bb68c69__notion-fetch` with id `ac84c676ad7249d2a79732d842f71d62`.
- Connector returns database schema (even partial) → ✅ Notion live. Note in audit trail. **Do NOT alert.** This is the healthy steady state — the connector is the endpoint the morning sync actually uses.
- Connector returns 404 or auth error → fall back to `mcp__plugin_Notion_notion__notion-fetch` (same id).
  - Fallback works → ✅ Notion live (via plugin). Note in audit trail, no alert.
  - Both fail → 🔴 add to unresolved list: "Both Notion endpoints disconnected — GATE 1 milestone check will be skipped in tomorrow's sync. Re-auth: open Claude Code, run Notion OAuth, select firstraingroup workspace."

> **Do NOT report "Notion primary endpoint needs re-auth" when the connector is live.** The old `plugin:Notion:notion` endpoint is OAuth-based and expires every few days; it cannot re-auth headless. It is NO LONGER primary — its being unauthenticated is expected and harmless as long as the connector serves the tracker. Alert ONLY when the milestone data genuinely cannot be fetched (both endpoints down). This inversion is what stops the daily false alarm.

**Google Drive (Cashflow Master sheet):**
Call `mcp__a9a30244-5e56-4840-804f-19f9622e0bf6__get_file_metadata` with fileId `1kBYFQfER46gAqcnCA2jaGkjG_h4iEHj4c6EDVVvREKA`.
- Returns file metadata (title, mtime, owner) → ✅ Drive live + file accessible.
- Returns auth error or 404 → 🔴 add to unresolved list: "Google Drive MCP disconnected or Cashflow Master inaccessible — morning sync Step 5C (sheet download) will fail. All 3 Drive retry attempts will exhaust and fall back to cached xlsx. Re-auth: check Google Drive MCP OAuth in Claude Code settings."

**Gmail:**
Call `mcp__gmail__list_labels` with no arguments.
- Returns label list (including `Finance/HDFC-Txn`) → ✅ Gmail live.
- `Finance/HDFC-Txn` label missing from results → ⚠️ add to healed list: "Gmail connected but Finance/HDFC-Txn label not found — HDFC transaction alerts may not route correctly. Verify label exists in Gmail settings."
- Returns auth error or timeout → 🔴 add to unresolved list: "Gmail MCP disconnected — morning sync Steps 3 (client emails), 5E (HDFC fetch), and Step 9 (Gmail draft) will all fail. Re-auth: check Gmail MCP OAuth in Claude Code settings."

**FRBIS (MongoDB):** Connect from `.secrets/frbis.env` per `.claude/frbis-sync.md`, then call
`mcp__plugin_mongodb_mongodb__find` on db `frbis` collection `briefs` with `limit:1` (cheap liveness probe).
- Returns a document → ✅ FRBIS live. Note in audit trail.
- Connect or find errors / tool-not-found → 🔴 add to unresolved list: "FRBIS MongoDB MCP disconnected — the morning/midday/EOD FRBIS brief-pipeline block will be empty. Re-check the MongoDB MCP and `.secrets/frbis.env`."
- ALSO verify freshness: confirm today's `_outputs/briefing-YYYY-MM-DD.md` contains a `🎨 FRBIS` section. If the briefing exists but has NO `🎨 FRBIS` line → ⚠️ add to note list: "Morning briefing missing the FRBIS block — STEP 2B may have failed silently."

Run all 5 pings in ONE parallel message — do not serialise them.

Record results as: `MCP health: Bigin ✅/🔴 · Notion ✅/⚠️/🔴 · Drive ✅/🔴 · Gmail ✅/⚠️/🔴 · FRBIS ✅/🔴`

## STEP 6 — Telegram (ALWAYS send)

**HEADLESS DELIVERY — do this FIRST, before anything else in this step:** compose the message below, then write it VERBATIM (overwrite) to `_outputs/telegram-outbox/first-rain-heal-check.txt`. On scheduled (launchd) runs the `plugin:telegram` MCP is NOT connected, so the driver reads this file and delivers it via Telegram after the run — this is the path that actually reaches Niloy. Writing this file is mandatory and must not be skipped.

Then also attempt a Telegram via `mcp__plugin_telegram_telegram__reply` (chat_id `"8770250893"`) — this delivers on interactive runs; in headless it fails harmlessly and the driver delivers from the outbox file (do not treat that failure as an error).

**Format by outcome:**

All checks green, nothing healed:
```
🩺 Heal check · <date> · ✅ All systems green
```

Auto-healed something, no remaining failures:
```
🩺 Heal check · <date>

⚠️ Healed:
- <action> ✅
…
```

Any 🔴 failure that could not be fixed:
```
🩺 Heal check · <date>

🔴 Unresolved — action needed:
- <issue>
…
```

Stay under 4000 chars. Never skip this step — Niloy expects the heartbeat every day.

**Gmail fallback (if Telegram call fails or returns error):**
If `mcp__plugin_telegram_telegram__reply` fails for any reason, immediately call `mcp__gmail__create_draft` with:
- to: `["niloy@firstrain.co.in"]`
- subject: `⚠️ PIPELINE ALERT [date] — Telegram MCP down, heal-check could not notify`
- body: same content that would have gone to Telegram (list of healed items and/or unresolved failures)

This ensures at least one notification channel delivers the alert even if Telegram is unreachable. Log: "Telegram failed — Gmail fallback draft created."

## STEP 7 — Audit trail in briefing

Append a `## HEAL CHECK <HH:MM IST>` section to `_outputs/briefing-YYYY-MM-DD.md`:

```
## HEAL CHECK [HH:MM IST]
Status: ✅ All green | ⚠️ Healed [N] items | 🔴 [N] unresolved failures
[List auto-healed items if any]
[List unresolved failures if any]
MCP health: Bigin ✅/🔴 · Notion ✅/⚠️/🔴 · Drive ✅/🔴 · Gmail ✅/⚠️/🔴 · FRBIS ✅/🔴
Telegram sent: yes · msg <id> | failed — Gmail fallback used
```

The briefing file is the single audit trail — don't write a second file unless the briefing is missing.

## RULES (don't break these)
- Code regex fixes (e.g. HDFC parser) require a human — DETECT and quote the failing snippet, never auto-edit Python.
- Don't run `git commit` from this task — committing daily artefacts is Niloy's choice, not yours.
- Don't re-run the full briefing (Telegram blast, Gmail draft). The morning task already did that.
- All Python scripts run from vault root, never from a worktree.
- Stay under 4000 chars in any Telegram message.
- Always send Step 6 Telegram — even "✅ All systems green." Niloy needs the heartbeat to know the check ran.