# /finance — First Rain Cash & Projects Dashboard · Daily Build
# Architecture A: Claude calls MCP (Bigin + Google Drive + Gmail) → writes JSON → runs Python → renders HTML.
# Runs daily at 08:00 IST. Pipeline + project economics + cash position + bank flow.
#
# ⚠️ ALL Python scripts MUST run from the vault root:
#    cd ~/Desktop/Andrej_Karpathy_Obsidian_FirstRain_Brain
# Never run scripts from a worktree (e.g. .claude/worktrees/...) — paths will be wrong.

## Data source ownership
| Source | Owns | Output file |
|---|---|---|
| Bigin (MCP) | Pipeline status: stage, amount, exec, region, industry | `data/projects/bigin_pipeline_raw.json` |
| Google Sheet `FirstRain-Cashflow-Master` (Drive MCP, all 8 tabs) | Cash, Treasury, Receivables, Payables, Invoices_Raised, Statutory, Notes, Projects | `data/projects/sheet_*.json` (8 files) |
| Gmail `niloy@firstrain.co.in` (HDFC alerts) | Bank transactions: NACH/UPI/ACH/credit/cheque/FCY | `data/projects/sheet_bank_transactions.json` |
| Gmail `niloy@firstrain.co.in` (collections) | Collection status | Collect tab only — NOT this command |
| FRBIS MongoDB (MCP, read-only) | Design-brief pipeline: status, designer, design-cut SLA | Reported inline (Step 12.5) — NOT written to cashflow.json |

**Known gap:** GST/TDS portal acks land in Ravindra's inbox (Sonal's accountant), NOT Niloy's. `/finance` cannot pull statutory filing confirmations. Workaround: Sonal updates the `Statutory` tab manually after Ravindra forwards GSTR/TDS challan PDFs. See Step 4 for what `Statutory` is expected to contain.

---

## Step 1 — Fetch Bigin pipeline (MCP)

Use `mcp__bigin__Bigin_getRecordsUsingCoqlQuery` (the Bigin-specific MCP — NOT the Zoho CRM one). First try with `Region`:

```sql
SELECT id, Deal_Name, Account_Name.id, Account_Name.Account_Name, Amount, Closing_Date, Stage, Pipeline, Probability, Created_Time, Modified_Time, Region, Owner.id FROM Pipelines WHERE Pipeline = 'Sales Pipeline 26-27'
```

**Known quirks:**
- **Result exceeds the tool-output token limit (expected — ~125 deals ≈ 53k chars).** The COQL result will NOT fit in main context; the MCP auto-saves it to a `tool-results/…txt` file and returns the path. Do NOT try to read it inline. Either (a) dispatch the whole of Step 1 (COQL → Accounts industry query → normalize → write `bigin_pipeline_raw.json`) to a subagent with the Agent tool, or (b) process the saved file with `jq`/`python` directly. The subagent path is preferred — it keeps the 125-deal dump out of the orchestrator context. The `WHERE id IN (...)` Accounts query is capped at ~50 ids and may need quoting around numeric ids; split into batches of ≤50 if it errors.
- `Owner.name` errors in COQL — always omit it. Use `Owner.id` only.
- The COQL `WHERE Pipeline = 'Sales Pipeline 26-27'` filter may return all pipeline records if the pipeline name doesn't match exactly. In that case, use `mcp__bigin__Bigin_getRecords` with `module_api_name=Pipelines`, `sort_by=Created_Time`, `sort_order=desc`, `per_page=200`, and filter in Python to `Created_Time >= '2026-03-01'` excluding stages `{Projections 25-26, Closed Won 25-26, Closed Won 24-25, Closed Won 23-24, Closed Won 22-23}`.
- If `Region` errors, retry without it — `classify_pipeline.py` applies regex fallback.

Then collect unique account_ids from the results and query Accounts for Industry:

```sql
SELECT id, Account_Name, Industry FROM Accounts WHERE id IN (<comma-separated account_ids>)
```

If Industry errors, retry without it and proceed — `classify_pipeline.py` applies regex fallback.

Normalize each deal using this mapping:

```python
import re

# Owner name not available in COQL — extract exec from deal name prefix
def extract_exec(deal_name):
    m = re.match(r'^(CK|DS|SP|ND)\s*[-–]', deal_name or '')
    return m.group(1) if m else None

owner_map = {"chinmay": "CK", "shilpa": "SP", "dhruv": "DS", "niloy": "ND"}
# Try owner name first (if available), else fall back to deal name prefix
exec_code = next((v for k, v in owner_map.items() if k in owner_name.lower()), None) or extract_exec(deal_name)

normalized_deal = {
    "id": row["id"],
    "deal": row["Deal_Name"],
    "account": account_id,           # from Account_Name.id
    "account_name": account_name,    # from Account_Name.Account_Name
    "amount": float(row.get("Amount") or 0),
    "prob": float(row.get("Probability") or 0),
    "stage": row.get("Stage"),
    "close": row.get("Closing_Date"),
    "created": row.get("Created_Time"),
    "modified": row.get("Modified_Time"),
    "industry": account_index.get(account_id, {}).get("Industry"),  # None if field absent
    "region": row.get("Region"),     # None if field absent
    "exec": exec_code,
}
```

Write the normalized result to `data/projects/bigin_pipeline_raw.json`:

```json
{
  "deals": [ /* list of normalized deals */ ],
  "meta": {
    "region_available": false,
    "industry_available": false,
    "fetched_at": "<ISO8601 timestamp>",
    "count": <N>
  }
}
```

---

## Step 2 — Classify pipeline (Python)

Run:
```bash
cd ~/Desktop/Andrej_Karpathy_Obsidian_FirstRain_Brain && python3 scripts/projects/classify_pipeline.py
```

Reads `data/projects/bigin_pipeline_raw.json` → writes `data/projects/bigin_pipeline_classified.json`.
Applies region + industry regex fallback for any deal with null values from Bigin.

---

## Step 3 — Download FirstRain-Cashflow-Master xlsx (Drive MCP)

**Source of truth: Google Sheet, NOT desktop xlsx.** Sonal edits the Sheet; we never touch her desktop file. The xlsx on Niloy's Desktop is only the schema template we built in `scripts/projects/add_projects_tab_to_xlsx.py` for reference.

Call `mcp__google-drive__download_file_content` with:
- `fileId`: `1kBYFQfER46gAqcnCA2jaGkjG_h4iEHj4c6EDVVvREKA`
- `mimeType`: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`

The MCP returns a JSON tool result containing `{content: [{embeddedResource: {contents: {blob: "<base64>", mimeType: "..."}}}]}` and saves it to a sandboxed tool-results path. **Copy the path the MCP prints in its info/error message** — directory enumeration is blocked, so auto-detect doesn't work.

Then decode to the cache:
```bash
cd ~/Desktop/Andrej_Karpathy_Obsidian_FirstRain_Brain && python3 scripts/projects/decode_drive_blob_to_cache.py <path_from_mcp_message>
```

This writes `data/projects/_cache/cashflow_master.xlsx` (~50 KB).

**Alternative if `decode_drive_blob_to_cache.py` is missing:** The Drive MCP returns `{content: "<base64>", ...}` saved to a tool-results file. Decode inline:
```bash
cd ~/Desktop/Andrej_Karpathy_Obsidian_FirstRain_Brain && python3 -c "
import json, base64, os
with open('<path_from_mcp_message>') as f: d = json.loads(f.read())
os.makedirs('data/projects/_cache', exist_ok=True)
open('data/projects/_cache/cashflow_master.xlsx', 'wb').write(base64.b64decode(d['content']))
print('done', os.path.getsize('data/projects/_cache/cashflow_master.xlsx'), 'bytes')
"
```

---

## Step 4 — Parse all 8 tabs from cached xlsx (Python)

```bash
cd ~/Desktop/Andrej_Karpathy_Obsidian_FirstRain_Brain && python3 scripts/projects/read_cashflow_xlsx.py
```

Reads `data/projects/_cache/cashflow_master.xlsx` → writes 8 JSON files to `data/projects/`:

| Tab | Output | Owner | Update freq |
|---|---|---|---|
| `Cash_Position` | `sheet_cash_position.json` | Sonal | Daily |
| `Treasury_Holdings` | `sheet_treasury.json` | Sonal | Weekly |
| `Receivables` | `sheet_receivables.json` | Sonal | Daily |
| `Payables` | `sheet_payables.json` | Sonal + Niloy | Daily |
| `Invoices_Raised` | `sheet_invoices_raised.json` | Sonal | Per invoice |
| `Statutory` | `sheet_statutory.json` | Sonal (Ravindra forwards acks) | Monthly |
| `Notes` | `sheet_notes.json` | Niloy | Ad hoc |
| `Projects` | `sheet_projects.json` | Niloy + Sonal | Per project closure |

Pre-flight check fails with **exit 3** + a friendly hint if the Sheet still has the old structure (tabs like `Cash & Burn`, `Project CM%`). When that happens, the message is: *"Sheet `FirstRain-Cashflow-Master` still has old structure. Required tabs: Cash_Position, Treasury_Holdings, Receivables, Payables, Invoices_Raised, Statutory, Notes, Projects. Niloy needs to migrate."*

If exit 3: stop the pipeline, post to Telegram chat `8770250893` with the migration hint, do not continue.

---

## Step 5 — Fetch HDFC bank transaction emails (Gmail MCP)

Call `mcp__gmail__search_threads` with:
- `query`: `label:finance-hdfc-txn newer_than:60d`
- `pageSize`: `100`

The label `Finance/HDFC-Txn` is maintained by a Gmail filter Niloy set up (see `_context/team-map.md` or just check Gmail Settings → Filters). The filter sender list is the source of truth for which HDFC senders count as "transaction" — if it changes, only the filter needs updating, not the script. The sender allowlist inside `parse_hdfc_emails.py` (`BANK_SENDER_DOMAINS`, `NON_BANK_SENDERS`) is now defense-in-depth, not the primary gate.

The MCP returns JSON shaped `{threads: [{id, messages: [{date, sender, snippet, subject, ...}]}]}`. Save the response verbatim to `data/projects/_cache/hdfc_emails.json` (use the Write tool with the JSON content).

If `nextPageToken` is present in the response, fetch a second page with `pageToken: <nextPageToken>` and merge `threads` arrays into the same cache file before passing to the parser.

---

## Step 5b — Scan deal-status emails (Gmail MCP, including CC'd)

Call `mcp__gmail__search_threads` with:
- `query`: `(Secure OR Amaara OR Nordex OR Nutriventia OR Iberchem OR Brenntag OR Coats OR Jyothi OR DOTTS) newer_than:2d (to:niloy@firstrain.co.in OR from:niloy@firstrain.co.in OR cc:niloy@firstrain.co.in)`
- `pageSize`: `20`

For each thread found, check if it signals a deal status change vs what Bigin/sheet shows:
- Quote sent → stage = Price Quote (not Design)
- Client reply received → remove "no reply" / "follow up" language from that deal item
- Payment confirmed → update receivables status
- New terms / delays → note in the relevant deal item in the briefing

**Rules:**
- Surface changes as delta lines in the briefing: `⚡ [Client] — [what changed] (email [date])`
- Never say "no reply" or "push design" if this scan shows the action already happened
- If no deal-email threads found: skip silently — do not warn
- This scan is read-only — never update Bigin or the sheet here

**HDFC iMessage cross-check (cash variation line):**
Also check `data/projects/sheet_bank_transactions.json` → `latestBalance`. If the HDFC iMessage-derived balance differs from `sheet_cash_position.json` → `operatingCash` by more than ₹1L, surface as:
`⚠️ Cash: ₹XX.XXL (Sonal's sheet) | HDFC alert shows ₹YY.YYL — gap ₹ZZ.ZZL. Confirm with Sonal.`

---

## Step 6 — Parse HDFC emails (Python)

```bash
cd ~/Desktop/Andrej_Karpathy_Obsidian_FirstRain_Brain && python3 scripts/projects/parse_hdfc_emails.py data/projects/_cache/hdfc_emails.json
```

Reads the cached threads → writes `data/projects/sheet_bank_transactions.json` with:
- `transactions`: deduplicated list (NACH+ACH twin alerts collapsed automatically)
- `totals`: `{credits, debits, net, transactionCount, fcyPendingCount}` — INR only, FCY excluded
- `latestBalance`: most recent BALANCE_SNAPSHOT
- `fcyPending`: FCY inward / disposal entries needing FX conversion
- `meta.unparseableCount` should be **0** under normal conditions

If `unparseableCount > 0`: HDFC has changed an alert template. Inspect `meta.warnings[]` and patch a regex in `parse_hdfc_emails.py`. Do not silently ignore.

---

## Step 7 — Compute momentum (Python)

```bash
cd ~/Desktop/Andrej_Karpathy_Obsidian_FirstRain_Brain && python3 scripts/projects/compute_momentum.py
```

Reads `bigin_pipeline_classified.json` → writes `momentum.json` + appends daily snapshot to `data/projects/snapshots/YYYY-MM-DD.json`.

First run will produce `mode: "snapshot_only"` — this is expected. Upgrades to `partial` after 2 days, `full` after 7 days.

---

## Step 8 — Drift check (Python)

```bash
cd ~/Desktop/Andrej_Karpathy_Obsidian_FirstRain_Brain && python3 scripts/projects/drift_check.py
```

Reads `bigin_pipeline_classified.json` + `sheet_projects.json` → writes `drift_report.json`.

---

## Step 9 — Render dashboard (Python)

```bash
cd ~/Desktop/Andrej_Karpathy_Obsidian_FirstRain_Brain && python3 scripts/projects/build_cashflow_json.py --from-files
```

Reads all 10 JSON files (`bigin_pipeline_classified.json`, 8× `sheet_*.json`, `sheet_bank_transactions.json`) → writes `data/projects/cashflow.json` → renders `dashboards/dashboard.html`.

If this fails with a missing-file error, check which step didn't write its output.

---

## Step 10 — Validate

Validation checklist (required before declaring success):
- [ ] `dashboards/dashboard.html` exists and contains `{{CASHFLOW_JSON}}` substituted (not the literal placeholder)
- [ ] 0 instances of `NaN` in the rendered HTML, and 0 *data-injected* `undefined`. NOTE: the template's own JS contains exactly one legitimate `actualPct !== undefined` guard — that single match is expected and is NOT a failure. Check with: `grep -oE '.{0,30}undefined.{0,30}' dashboards/dashboard.html` — if the only hit is the `!== undefined` guard, validation passes. Any `undefined` appearing inside the injected JSON data block IS a failure.
- [ ] `drift_report.json` has `counts.ALERT` and `counts.WARNING` keys (not missing keys)
- [ ] `momentum.json` has `mode` key (one of: snapshot_only / partial / full)
- [ ] `sheet_bank_transactions.json` `meta.unparseableCount` is 0
- [ ] `sheet_cash_position.json` operatingCash ≥ ₹76,50,000 — **if below, escalate immediately per CLAUDE.md**

---

## Step 11 — Open + publish dashboard

Once Step 10 validation passes, do BOTH:

1. **Open locally for Niloy** (instant view, no auth):
```bash
cd ~/Desktop/Andrej_Karpathy_Obsidian_FirstRain_Brain && open dashboards/dashboard.html
```

2. **Publish to Cloudflare Pages for Sonal + remote access**:
```bash
cd ~/Desktop/Andrej_Karpathy_Obsidian_FirstRain_Brain && bash scripts/deploy_dashboard.sh
```

**This is the ONLY way to deploy.** `scripts/deploy_dashboard.sh` is the single source of truth — the interactive `/finance`, the 9:08 AM `first-rain-monday-sync` cron, and the 10:05 AM `first-rain-heal-check` all call this exact line. Never inline a raw `wrangler pages deploy` command anywhere: that is what caused the May–Jun 2026 daily-stale-dashboard bug (the cron copies were missing `source .secrets/cloudflare.env`, so headless deploys silently failed while the interactive copy worked).

The script prints one machine-parseable final line — `DEPLOY_RESULT=OK url=... canonical=401` or `DEPLOY_RESULT=FAIL reason=... detail="..."` — and writes the same to `data/projects/deploy_status.json`. **Report deploy status from that line / that file. Never narrate a "headless gap."**

**Auth:** the script sources `CLOUDFLARE_API_TOKEN` from `.secrets/cloudflare.env` (gitignored, chmod 600) — a persistent API token (Account → Cloudflare Pages → Edit, no expiry), set up 01 Jun 2026 to replace the OAuth login that kept expiring. **Do NOT rely on `wrangler login` OAuth** — it breaks the cron. If `DEPLOY_RESULT=FAIL reason=no_token`, the token was revoked or the file is missing — recreate at https://dash.cloudflare.com/profile/api-tokens and rewrite `.secrets/cloudflare.env` as `export CLOUDFLARE_API_TOKEN=...`.

The Cloudflare URL is `https://firstrain-dashboard.pages.dev` — gated by HTTP Basic Auth via `dashboards/_worker.js`. Password is in the Pages env var `DASHBOARD_PASSWORD` (set in Cloudflare dashboard → Pages → firstrain-dashboard → Settings → Variables and Secrets, encrypted). Sonal has the password.

If the wrangler step fails, log the failure but DON'T abort — local view is still good. Telegram an alert: *"Cloudflare deploy failed at [time] — Sonal dashboard stale."*

Do both **after** validation. Never publish a broken dashboard.

---

## Step 12 — Emit daily briefing (Telegram + Gmail Draft)

**Always run this step — not conditional on alerts.**

All three outputs must come from the same `cashflow.json["FR"]["telegramBriefing"]` string so they are guaranteed consistent. Never reconstruct the briefing text from scratch here — read the pre-built string from the JSON.

```python
import json
d = json.load(open("data/projects/cashflow.json"))
briefing_text = d["FR"]["telegramBriefing"]
today_str = d["META"]["today"]          # e.g. "25 May 2026"
```

**12a — Telegram (always send)**

Send to chat_id `8770250893`:
```
{briefing_text}
```
Use `mcp__plugin_telegram_telegram__reply` with `chat_id: "8770250893"`.

**12b — Gmail Draft (always create)**

Call `mcp__gmail__create_draft` with:
- `to`: `niloy@firstrain.co.in`
- `subject`: `First Rain Daily · {today_str}`
- `body`: `{briefing_text}`

This draft stays in Drafts until Niloy sends or discards — it is the paper trail for the day's cash position.

**Consistency rule**: Dashboard HTML, Telegram message, and Gmail Draft all carry identical content because all three read from `cashflow.json["FR"]["telegramBriefing"]`. If you ever need to regenerate just the HTML (e.g. after a template fix), re-run Step 9+11 AND re-emit Steps 12a+12b so all three stay in sync.

---

## Step 12.5 — FRBIS brief pipeline (MongoDB MCP, read-only)

Pull and bucket the design-brief pipeline per `.claude/frbis-sync.md` (connect from
`.secrets/frbis.env`, pull all briefs, bucket in-head). Emit the **morning / midday / eod**
variant from that spec based on the current IST time. This surfaces design-cut SLA health
(overdue cuts, unclaimed briefs, synthesis pending) alongside cash — the delivery side of the
business the cash dashboard doesn't see.

Print it as a standalone block in the interactive output. **Do not** write it into
`cashflow.json` or the Python-built `telegramBriefing` — this step is report-only and must not
touch the dashboard pipeline. If FRBIS won't connect, print "FRBIS DISCONNECTED" and continue;
never let it block the finance run.

---

## Step 13 — Report

Print summary:
```
/finance · [YYYY-MM-DD]
Bigin: [N] deals  Region: [bigin|regex]  Industry: [bigin|regex]
Sheet: 8 tabs parsed (cash ₹X.XL · treasury ₹Y.YL · [N] receivables · [N] payables · [N] projects)
HDFC: [N] txns over 60d  Credits ₹X.XL  Debits ₹Y.YL  Net ₹Z.ZL  LatestBal ₹B.BL (acct NNNN)
Drift: [N] ALERT · [N] WARNING · [N] INFO
Momentum: [mode] ([N] snapshots)
FRBIS: [N] briefs ([n] New / [n] Active / [n] Done) · [n] overdue cuts · [n] synth pending
Dashboard: dashboards/dashboard.html ✓ (opened locally) · https://firstrain-dashboard.pages.dev ✓ (published)
Telegram: sent ✓ · Gmail Draft: created ✓
```

---

## Error handling

| Error | Action |
|---|---|
| Bigin COQL returns 0 deals | Stop. Report: "Bigin returned 0 deals — check pipeline name or MCP auth." |
| Drive MCP `download_file_content` fails | Check that file ID `1kBYFQfER46gAqcnCA2jaGkjG_h4iEHj4c6EDVVvREKA` is still shared with the Drive MCP service account. |
| `read_cashflow_xlsx.py` exit 3 (missing required tabs) | Stop. Sheet still has old structure. Post to Telegram with migration list. Do not continue. |
| Gmail MCP returns 0 HDFC threads | Likely auth issue. Stop. Re-authorize Gmail MCP. |
| `parse_hdfc_emails.py` `unparseableCount > 0` | HDFC changed an alert template. Inspect warnings, patch a regex, re-run. Do not skip. |
| `build_cashflow_json.py --from-files` fails | Check which JSON file is missing. Re-run from that step. |
| Template missing `{{CASHFLOW_JSON}}` | Report: "dashboard-template.html missing substitution marker — re-check dashboards/ folder." |
| Telegram send fails (Step 12a) | Log the error; still create Gmail Draft. Never skip both. |
| Gmail Draft creation fails (Step 12b) | Log the error; verify Telegram was sent. Never skip both. |

---

## Architecture note for future evolution

**Cash Flow tab still paused** (see `_context/active-projects.md` and the memory note `project_cashflow_tab_wiring.md`). Three of five Cash Flow data sources are wired (inRecv from Receivables, inPipeline from Bigin, outVendors from Payables). Outflows for payroll + statutory monthly splits are still blocked on Niloy's pick from three options. Until that's resolved, the Cash Flow tab in the dashboard renders 3-of-5 fields. Don't try to fix it inside `/finance` — wait for the unblock.
