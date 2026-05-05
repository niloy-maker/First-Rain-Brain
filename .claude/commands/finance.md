# /finance — First Rain Cash & Projects Dashboard · Daily Build
# Architecture A: Claude calls MCP (Bigin + Google Drive + Gmail) → writes JSON → runs Python → renders HTML.
# Runs daily at 08:00 IST. Pipeline + project economics + cash position + bank flow.

## Data source ownership
| Source | Owns | Output file |
|---|---|---|
| Bigin (MCP) | Pipeline status: stage, amount, exec, region, industry | `data/projects/bigin_pipeline_raw.json` |
| Google Sheet `FirstRain-Cashflow-Master` (Drive MCP, all 8 tabs) | Cash, Treasury, Receivables, Payables, Invoices_Raised, Statutory, Notes, Projects | `data/projects/sheet_*.json` (8 files) |
| Gmail `niloy@firstrain.co.in` (HDFC alerts) | Bank transactions: NACH/UPI/ACH/credit/cheque/FCY | `data/projects/sheet_bank_transactions.json` |
| Gmail `niloy@firstrain.co.in` (collections) | Collection status | Collect tab only — NOT this command |

**Known gap:** GST/TDS portal acks land in Ravindra's inbox (Sonal's accountant), NOT Niloy's. `/finance` cannot pull statutory filing confirmations. Workaround: Sonal updates the `Statutory` tab manually after Ravindra forwards GSTR/TDS challan PDFs. See Step 4 for what `Statutory` is expected to contain.

---

## Step 1 — Fetch Bigin pipeline (MCP)

Use `mcp__claude_ai_Bigin__Bigin_getRecordsUsingCoqlQuery` with this query:

```sql
SELECT id, Deal_Name, Account_Name.id, Account_Name.Account_Name, Amount, Closing_Date, Stage, Pipeline, Probability, Created_Time, Modified_Time, Region, Owner.id, Owner.name FROM Pipelines WHERE Pipeline = 'Sales Pipeline 26-27'
```

If the query errors on `Region` (field not yet configured in Bigin admin), retry without it:

```sql
SELECT id, Deal_Name, Account_Name.id, Account_Name.Account_Name, Amount, Closing_Date, Stage, Pipeline, Probability, Created_Time, Modified_Time, Owner.id, Owner.name FROM Pipelines WHERE Pipeline = 'Sales Pipeline 26-27'
```

Then collect unique account_ids from the results and query Accounts for Industry:

```sql
SELECT id, Account_Name, Industry FROM Accounts WHERE id IN (<comma-separated account_ids>)
```

If Industry errors, retry without it and proceed — `classify_pipeline.py` applies regex fallback.

Normalize each deal using this mapping (from `scripts/projects/fetch_bigin_pipeline.py`):

```python
owner_map = {"chinmay": "CK", "shilpa": "SP", "dhruv": "DS", "niloy": "ND"}
exec_code = next((v for k, v in owner_map.items() if k in owner_name.lower()), None)

normalized_deal = {
    "id": row["id"],
    "deal": row["Deal_Name"],
    "account": account_id,           # from Account_Name.id
    "account_name": account_name,    # from Account_Name.Account_Name
    "amount": float(row["Amount"] or 0),
    "prob": float(row["Probability"] or 0),
    "stage": row["Stage"],
    "close": row["Closing_Date"],
    "created": row["Created_Time"],
    "modified": row["Modified_Time"],
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
    "region_available": true,
    "industry_available": true,
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

Call `mcp__a9a30244-5e56-4840-804f-19f9622e0bf6__download_file_content` with:
- `fileId`: `1kBYFQfER46gAqcnCA2jaGkjG_h4iEHj4c6EDVVvREKA`
- `mimeType`: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`

The MCP returns a JSON tool result containing `{content: [{embeddedResource: {contents: {blob: "<base64>", mimeType: "..."}}}]}` and saves it to a sandboxed tool-results path. **Copy the path the MCP prints in its info/error message** — directory enumeration is blocked, so auto-detect doesn't work.

Then decode to the cache:
```bash
python3 scripts/projects/decode_drive_blob_to_cache.py <path_from_mcp_message>
```

This writes `data/projects/_cache/cashflow_master.xlsx` (~50 KB).

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

Call `mcp__211f86be-24d9-4ad8-8c8e-2454fa7eff51__search_threads` with:
- `query`: `label:finance-hdfc-txn newer_than:60d`
- `pageSize`: `100`

The label `Finance/HDFC-Txn` is maintained by a Gmail filter Niloy set up (see `_context/team-map.md` or just check Gmail Settings → Filters). The filter sender list is the source of truth for which HDFC senders count as "transaction" — if it changes, only the filter needs updating, not the script. The sender allowlist inside `parse_hdfc_emails.py` (`BANK_SENDER_DOMAINS`, `NON_BANK_SENDERS`) is now defense-in-depth, not the primary gate.

The MCP returns JSON shaped `{threads: [{id, messages: [{date, sender, snippet, subject, ...}]}]}`. Save the response verbatim to `data/projects/_cache/hdfc_emails.json` (use the Write tool with the JSON content).

If `nextPageToken` is present in the response, fetch a second page with `pageToken: <nextPageToken>` and merge `threads` arrays into the same cache file before passing to the parser.

---

## Step 6 — Parse HDFC emails (Python)

```bash
python3 scripts/projects/parse_hdfc_emails.py data/projects/_cache/hdfc_emails.json
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
python3 scripts/projects/compute_momentum.py
```

Reads `bigin_pipeline_classified.json` → writes `momentum.json` + appends daily snapshot to `data/projects/snapshots/YYYY-MM-DD.json`.

First run will produce `mode: "snapshot_only"` — this is expected. Upgrades to `partial` after 2 days, `full` after 7 days.

---

## Step 8 — Drift check (Python)

```bash
python3 scripts/projects/drift_check.py
```

Reads `bigin_pipeline_classified.json` + `sheet_projects.json` → writes `drift_report.json`.

---

## Step 9 — Render dashboard (Python)

```bash
python3 scripts/projects/build_cashflow_json.py --from-files
```

Reads all 10 JSON files (`bigin_pipeline_classified.json`, 8× `sheet_*.json`, `sheet_bank_transactions.json`) → writes `data/projects/cashflow.json` → renders `dashboards/dashboard.html`.

If this fails with a missing-file error, check which step didn't write its output.

---

## Step 10 — Validate

Validation checklist (required before declaring success):
- [ ] `dashboards/dashboard.html` exists and contains `{{CASHFLOW_JSON}}` substituted (not the literal placeholder)
- [ ] 0 instances of `NaN` or `undefined` in the rendered HTML
- [ ] `drift_report.json` has `counts.ALERT` and `counts.WARNING` keys (not missing keys)
- [ ] `momentum.json` has `mode` key (one of: snapshot_only / partial / full)
- [ ] `sheet_bank_transactions.json` `meta.unparseableCount` is 0
- [ ] `sheet_cash_position.json` operatingCash ≥ ₹76,50,000 — **if below, escalate immediately per CLAUDE.md**

---

## Step 11 — Open dashboard in browser

Once Step 10 validation passes:

```bash
open dashboards/dashboard.html
```

Do this **after** validation, never before — don't open a broken dashboard.

---

## Step 12 — Report

Print summary:
```
/finance · [YYYY-MM-DD]
Bigin: [N] deals  Region: [bigin|regex]  Industry: [bigin|regex]
Sheet: 8 tabs parsed (cash ₹X.XL · treasury ₹Y.YL · [N] receivables · [N] payables · [N] projects)
HDFC: [N] txns over 60d  Credits ₹X.XL  Debits ₹Y.YL  Net ₹Z.ZL  LatestBal ₹B.BL (acct NNNN)
Drift: [N] ALERT · [N] WARNING · [N] INFO
Momentum: [mode] ([N] snapshots)
Dashboard: dashboards/dashboard.html ✓ (opened in browser)
```

If drift ALERT count > 0 OR `operatingCash` below floor: send Telegram message to chat_id `8770250893` listing each issue (use `mcp__plugin_telegram_telegram__reply`).

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

---

## Architecture note for future evolution

**Cash Flow tab still paused** (see `_context/active-projects.md` and the memory note `project_cashflow_tab_wiring.md`). Three of five Cash Flow data sources are wired (inRecv from Receivables, inPipeline from Bigin, outVendors from Payables). Outflows for payroll + statutory monthly splits are still blocked on Niloy's pick from three options. Until that's resolved, the Cash Flow tab in the dashboard renders 3-of-5 fields. Don't try to fix it inside `/finance` — wait for the unblock.
