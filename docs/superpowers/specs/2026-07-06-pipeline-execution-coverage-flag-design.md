# Pipeline Coverage by Execution Month — Daily Briefing Flag

**Date:** 2026-07-06
**Status:** Approved design — ready for implementation plan
**Owner:** Niloy (requested); implemented in the /finance daily build

## Problem

The daily briefing tracks pipeline by **closing date**, which hides thin *execution* months. August 2026 surfaced this: by execution date it held only ₹14.4L of live work (one deal, Pharmatech) plus a lost ₹18.6L deal (FI India / Brenntag) — a near-empty delivery month that the close-date view never flagged. By the time a thin month is visible, it is too late to fill it (custom stands need ~6–8 weeks lead time).

## Goal

Add an automated flag to the daily briefing that tracks **pipeline coverage by execution month** and warns when a month has too little live execution work while there is still time to act.

**Rule:** a month with **< ₹40L** of live execution work should trigger a flag by the **T-10-week mark** (when the month is ~10 weeks out and still under-filled).

## Definitions

- **Execution month** — the month a project/show actually runs. Sourced from Bigin's `Project_Month` field (NOT `Closing_Date`).
- **Live execution work** (the metric compared against the floor) — sum of Bigin deal `Amount` for deals whose `Project_Month` falls in that month and whose bucket is **not** `lost` and **not** `junk`/not-qualified. This is effectively **Won + Existing Confirmed + Active** ("committed + active").
  - Rationale: counting open/active deals *only* would false-flag a sold-out month. July 2026 had ₹0 open pipeline yet was fully booked with ₹59.75L of Won work — it must read as full, not empty.
- **Floor** — default **₹40,00,000**, overridable via a `CONFIG_EXEC_COVERAGE_FLOOR` entry in Sonal's Notes tab (`sheet_notes.json`) with no code change.
- **T-10-week mark** — a month whose first day is ≤ 70 days from the build date.

## Approach (chosen: A — Bigin single-source)

Use Bigin's `Project_Month` + `bucket` for the entire metric. Bigin holds every deal (active, won, existing-confirmed) with an amount, and Bigin is the source of truth for deal amounts, so there is one source, no double-counting, and the metric is exactly "committed + active" by construction.

Rejected alternatives:
- **B — blend Bigin (active) + sheet `delivery_month` (committed):** Won deals appear in both Bigin and `sheet_projects.json` → double-count risk; sheet SP ≠ Bigin amount. More complex, no accuracy gain that matters here.
- **C — sheet-only:** the sheet has no active/open pipeline, so it cannot measure "committed + active".

## Design

### Part 1 — Prerequisite: pull execution month into the cache

The daily Bigin fetch (Step 1 of `.claude/commands/finance.md`) currently selects `Closing_Date` but not `Project_Month`.

- Add `Project_Month` to the COQL `SELECT` in the Step-1 fetch.
- Map it onto each normalized deal as `project_month` (ISO date string `YYYY-MM-DD`, or `null` when absent) in `data/projects/bigin_pipeline_raw.json`.
- `classify_pipeline.py` passes `project_month` through unchanged into `bigin_pipeline_classified.json`.

Without this field there is no execution-month data to compute on. This is the only change to the fetch/classify stage.

### Part 2 — Computation in `build_cashflow_json.py`

New pure function `_compute_pipeline_coverage_by_month(deals, today)`:

1. Bucket deals by `project_month[:7]` (`YYYY-MM`), skipping deals with `bucket in {lost, junk}` and deals with no `project_month`.
2. Per month accumulate:
   - `value` — Σ `amount` of included deals (unpriced deals contribute 0),
   - `deal_count` — number of included deals,
   - `unpriced_count` — included deals with `amount` null/0,
   - `committed_value` / `active_value` — split for context in the dashboard.
3. For **every** FY27 month (`2026-04` … `2027-03`): elapsed months (before the current month) get severity `PAST` — included in `months` for the full-year dashboard view (rendered muted), never flagged. For current/future months, compute `weeks_out = (month_first_day − today) / 7` (measured to the month's **first day**; the current month yields ≤ 0 and is clamped to 0 for display) and assign severity vs floor:
   - `weeks_out ≤ 10` **and** `value < floor` → **ALERT**
   - `10 < weeks_out ≤ ~18` (≈ 4 months) **and** `value < floor` → **INFO**
   - otherwise → no flag
4. Also compute `missing_exec_month_count` — count of live (non-lost, non-junk) deals with no `project_month`, so gaps don't hide silently.
5. Read the floor from `CONFIG_EXEC_COVERAGE_FLOOR` in `sheet_notes.json` if present, else default `4_000_000`.

Call site: inside `_compose_cashflow()` after `cashflow_months` is finalized. Write result to a new top-level key:

```json
"pipelineCoverageMeta": {
  "floor": 4000000,
  "generatedAt": "2026-07-06T08:00:00+05:30",
  "missingExecMonthCount": 3,
  "months": [
    {
      "month": "2026-08", "label": "Aug'26",
      "value": 1440000, "committedValue": 0, "activeValue": 1440000,
      "dealCount": 1, "unpricedCount": 0,
      "weeksOut": 4, "severity": "ALERT"
    }
  ],
  "flags": [ /* subset of months where severity in {ALERT, INFO}, ALERT first */ ]
}
```

### Part 3 — Briefing injection in `_build_telegram_briefing()`

Add a section after the Projects YTD block, shown **only when `flags` is non-empty** (matches existing alert style):

```
📅 EXECUTION COVERAGE
🔴 Aug'26: ₹14.4L booked vs ₹40L floor · ~4wk out — thin, salvage now
🟡 Oct'26: ₹22.0L vs ₹40L · ~12wk out — watch
```

- ALERT → 🔴, INFO → 🟡.
- If `missingExecMonthCount > 0`, append: `⚠️ N live deals missing execution month — coverage understated.`
- A thin month with `unpricedCount > 0` appends `(N unpriced)` so understated coverage is visible.

This string is sent to Telegram and rendered in the dashboard Alerts tab (both read the same `telegramBriefing` string), so it goes live in the next 08:00 build.

### Part 4 — Dashboard tab (in scope for v1)

Add a **"Execution Coverage"** section to the Pipeline tab of the dashboard, rendered from `pipelineCoverageMeta`:

- One row per upcoming month through FY27: month label, a horizontal bar of `value` against the `floor`, colour by severity (🔴 ALERT / 🟡 INFO / 🟢 OK), `weeksOut`, `dealCount`, and `unpricedCount`.
- A small caption stating the floor and the T-10-week rule.
- If `missingExecMonthCount > 0`, a one-line warning above the rows.

Rendering follows the existing dashboard template pattern (`dashboards/dashboard-template.html` → `{{CASHFLOW_JSON}}` substitution → `dashboards/dashboard.html`). Exact template location and the JS render hook are confirmed during implementation.

## Components & boundaries

| Unit | Responsibility | Input | Output |
|---|---|---|---|
| Step-1 fetch (finance.md) | pull `Project_Month` via MCP | Bigin COQL | `project_month` on each deal in `bigin_pipeline_raw.json` |
| `classify_pipeline.py` | pass-through | raw json | `project_month` in classified json |
| `_compute_pipeline_coverage_by_month()` | compute coverage + severity | classified deals + today | `pipelineCoverageMeta` dict |
| `_build_telegram_briefing()` | render flag lines | `pipelineCoverageMeta` | briefing text section |
| dashboard template + render JS | render coverage tab section | `pipelineCoverageMeta` | HTML |

The compute function is pure (deals + date in, dict out) so it is unit-testable in isolation with fixture deals.

## Testing

- Unit tests for `_compute_pipeline_coverage_by_month()` with fixtures covering: a thin month inside 10 weeks (ALERT), a thin month at ~14 weeks (INFO), a well-covered month (no flag), a sold-out month with only Won deals (no flag — regression against the July false-alarm), a month with unpriced deals (`unpricedCount` > 0), and deals with missing `project_month` (`missingExecMonthCount`).
- Verify floor override is picked up from `sheet_notes.json`.
- End-to-end: run the daily build against current cache and confirm `pipelineCoverageMeta` appears in `cashflow.json`, the briefing section renders when a flag exists (Aug'26 should ALERT today), and the dashboard tab renders. Existing Step-10 validation must still pass (no NaN/undefined).

## Out of scope

- No change to the close-date-based cashflow revenue projection (the existing `_monthly_revenue_from_bigin` 75/25 model stays as-is).
- No write-back to Bigin.
- No new scheduled task — the existing 08:00 daily build carries this once merged.

## Rollout

Merge before tomorrow's 08:00 IST build so the flag is live from the next daily briefing. Because Aug'26 is currently ~6 weeks out at ₹14.4L, the first run should emit a 🔴 ALERT for Aug'26.
