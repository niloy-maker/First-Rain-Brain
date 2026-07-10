# Pipeline Execution-Coverage Flag Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an automated daily-briefing flag that warns when a month has < ₹40L of live execution work (by Bigin `Project_Month`) while it is still inside the actionable window.

**Architecture:** Bigin single-source. Step 1 of `/finance` pulls `Project_Month` into the deal cache; a pure function in `build_cashflow_json.py` buckets live deals (bucket ∉ {lost, junk}) by execution month and assigns severity (ALERT ≤10 weeks out, INFO 10–18 weeks); the result lands in `cashflow.json["FR"]["pipelineCoverageMeta"]`, renders as a section in the Telegram briefing, and as a bar strip on the dashboard Projects page.

**Tech Stack:** Python 3 (stdlib only — json/datetime, matching existing scripts), `unittest` (matching `tests/projects/` convention), vanilla-JS string-built HTML in `dashboards/dashboard-template.html`.

**Spec:** `docs/superpowers/specs/2026-07-06-pipeline-execution-coverage-flag-design.md`

## Global Constraints

- ALL Python scripts run from the vault root: `cd ~/Desktop/Andrej_Karpathy_Obsidian_FirstRain_Brain` (never from a worktree — paths break).
- Floor default is exactly `4_000_000` (₹40L), overridable by a Notes-tab entry with category `CONFIG_EXEC_COVERAGE_FLOOR`.
- Severity windows: ALERT when `weeks_out ≤ 10`, INFO when `10 < weeks_out ≤ 18`, measured to the month's **first day**; current month clamps to 0.
- Coverage metric includes buckets `won`, `hot`, `active` (i.e. excludes `lost` and `junk`) — see `_bucket_stage()` in `scripts/projects/classify_pipeline.py:99-114`.
- First-run safety: if NO live deal carries `project_month`, `dataAvailable` must be `false` and `flags` must be empty (otherwise every month reads ₹0 and false-ALERTs).
- Data pulls are MCP-only: Python never calls Bigin; only the orchestrator (Claude via MCP) writes `bigin_pipeline_raw.json`. Task 7's re-fetch is orchestrator work, not a script.
- Deploys (if any) go through `bash scripts/deploy_dashboard.sh` — NEVER raw `wrangler pages deploy`.
- Commit messages end with `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`.
- Never `git add -A` — the vault working tree carries unrelated noise (.obsidian, .smart-env). Stage explicit paths only.

---

### Task 1: Branch + commit the approved spec

**Files:**
- Commit: `docs/superpowers/specs/2026-07-06-pipeline-execution-coverage-flag-design.md` (already written and approved)

**Interfaces:**
- Produces: branch `feat/exec-coverage-flag` that all later tasks commit to.

- [ ] **Step 1: Create the feature branch from current HEAD**

```bash
cd ~/Desktop/Andrej_Karpathy_Obsidian_FirstRain_Brain
git checkout -b feat/exec-coverage-flag
```

Expected: `Switched to a new branch 'feat/exec-coverage-flag'` (branching from `fix/hdfc-parser-dropped-txns` HEAD is fine — the working tree stays intact and only our files get committed).

- [ ] **Step 2: Commit the spec**

```bash
git add docs/superpowers/specs/2026-07-06-pipeline-execution-coverage-flag-design.md
git commit -m "docs: spec for pipeline execution-coverage flag

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 2: `_compute_pipeline_coverage_by_month()` (TDD)

**Files:**
- Modify: `scripts/projects/build_cashflow_json.py` (insert after `_monthly_revenue_from_bigin`, which ends at line 1296)
- Test: `tests/projects/test_execution_coverage.py` (new)

**Interfaces:**
- Consumes: module constants `_FY_MONTHS` (line 954, `["2026-04" … "2027-03"]`) and `REVENUE_STAGES` (line 1140, `{"closed won 26-27", "existing confirmed"}`); deal dicts as produced by `classify_pipeline.py` (keys: `deal`, `amount`, `stage`, `bucket`, `project_month`).
- Produces: `_compute_pipeline_coverage_by_month(deals: list[dict], today: datetime.date, floor: float = _COVERAGE_FLOOR_DEFAULT) -> dict` returning `{"floor": float, "dataAvailable": bool, "missingExecMonthCount": int, "months": [row…], "flags": [row…]}` where row = `{"month": "YYYY-MM", "label": "Aug'26", "value": float, "committedValue": float, "activeValue": float, "dealCount": int, "unpricedCount": int, "weeksOut": float, "severity": "ALERT"|"INFO"|"OK"}`. Tasks 3, 4, 6 depend on these exact key names.

- [ ] **Step 1: Write the failing tests**

Create `tests/projects/test_execution_coverage.py`:

```python
"""Execution-month pipeline coverage flag (spec 2026-07-06).

Pins the T-10-week thin-month trigger: a month with < floor of live execution
work (won + confirmed + active, bucketed by Bigin Project_Month) must ALERT
inside 10 weeks and INFO at 10-18 weeks.

Regression pinned: a fully-won month must NOT flag. July 2026 had zero open
pipeline but Rs 59.75L of Won work executing - reading a sold-out month as
"empty" was the failure mode the committed+active metric exists to avoid.

First-run safety pinned: before Step 1 of /finance carries Project_Month,
no deal has the field - every month would read Rs 0 and false-ALERT. The
dataAvailable=False guard suppresses all flags in that state.
"""
import sys, unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts" / "projects"))
from build_cashflow_json import _compute_pipeline_coverage_by_month

TODAY = date(2026, 7, 6)
FLOOR = 4_000_000


def deal(month, amount, bucket="active", stage="Requirement gathering"):
    return {"deal": "x", "project_month": month, "amount": amount,
            "bucket": bucket, "stage": stage}


class TestCoverageSeverity(unittest.TestCase):
    def test_thin_month_inside_10_weeks_alerts(self):
        cov = _compute_pipeline_coverage_by_month(
            [deal("2026-08-20", 1_440_000, "hot", "Price Quote")], TODAY, FLOOR)
        aug = next(m for m in cov["months"] if m["month"] == "2026-08")
        self.assertEqual(aug["severity"], "ALERT")
        self.assertIn(aug, cov["flags"])

    def test_thin_month_at_14_weeks_is_info(self):
        cov = _compute_pipeline_coverage_by_month(
            [deal("2026-10-15", 2_000_000)], TODAY, FLOOR)
        octr = next(m for m in cov["months"] if m["month"] == "2026-10")
        self.assertEqual(octr["severity"], "INFO")

    def test_covered_month_is_ok(self):
        cov = _compute_pipeline_coverage_by_month(
            [deal("2026-08-20", 5_000_000)], TODAY, FLOOR)
        aug = next(m for m in cov["months"] if m["month"] == "2026-08")
        self.assertEqual(aug["severity"], "OK")

    def test_sold_out_month_won_only_does_not_flag(self):
        # July regression: fully booked with Won work must read as full.
        cov = _compute_pipeline_coverage_by_month(
            [deal("2026-07-22", 5_975_000, "won", "Closed Won 26-27")], TODAY, FLOOR)
        jul = next(m for m in cov["months"] if m["month"] == "2026-07")
        self.assertEqual(jul["severity"], "OK")
        self.assertEqual(jul["committedValue"], 5_975_000)

    def test_lost_and_junk_excluded(self):
        deals = [deal("2026-08-26", 1_860_000, "lost", "Closed Lost"),
                 deal("2026-08-05", 9_900_000, "junk", "Not Qualified")]
        cov = _compute_pipeline_coverage_by_month(deals, TODAY, FLOOR)
        aug = next(m for m in cov["months"] if m["month"] == "2026-08")
        self.assertEqual(aug["value"], 0)
        self.assertEqual(aug["dealCount"], 0)

    def test_far_month_thin_is_quiet(self):
        # ~31 weeks out - distant months are supposed to be thin. No flag.
        cov = _compute_pipeline_coverage_by_month(
            [deal("2027-02-10", 100_000)], TODAY, FLOOR)
        feb = next(m for m in cov["months"] if m["month"] == "2027-02")
        self.assertEqual(feb["severity"], "OK")

    def test_unpriced_deals_counted(self):
        deals = [deal("2026-09-22", 0), deal("2026-09-16", 4_117_195)]
        cov = _compute_pipeline_coverage_by_month(deals, TODAY, FLOOR)
        sep = next(m for m in cov["months"] if m["month"] == "2026-09")
        self.assertEqual(sep["unpricedCount"], 1)
        self.assertEqual(sep["dealCount"], 2)

    def test_missing_project_month_counted_not_bucketed(self):
        deals = [deal("2026-08-20", 1_440_000),
                 {"deal": "no-pm", "amount": 500_000, "bucket": "active",
                  "stage": "Design", "project_month": None}]
        cov = _compute_pipeline_coverage_by_month(deals, TODAY, FLOOR)
        self.assertEqual(cov["missingExecMonthCount"], 1)
        self.assertTrue(cov["dataAvailable"])

    def test_no_project_month_data_at_all_suppresses_flags(self):
        deals = [{"deal": "no-pm", "amount": 500_000, "bucket": "active",
                  "stage": "Design"}]
        cov = _compute_pipeline_coverage_by_month(deals, TODAY, FLOOR)
        self.assertFalse(cov["dataAvailable"])
        self.assertEqual(cov["flags"], [])

    def test_floor_override(self):
        cov = _compute_pipeline_coverage_by_month(
            [deal("2026-08-20", 1_440_000)], TODAY, floor=1_000_000)
        aug = next(m for m in cov["months"] if m["month"] == "2026-08")
        self.assertEqual(aug["severity"], "OK")

    def test_alerts_precede_infos_in_flags(self):
        deals = [deal("2026-10-15", 100_000), deal("2026-08-20", 100_000)]
        cov = _compute_pipeline_coverage_by_month(deals, TODAY, FLOOR)
        sev = [f["severity"] for f in cov["flags"]]
        self.assertIn("ALERT", sev)
        self.assertIn("INFO", sev)
        first_info = sev.index("INFO")
        self.assertTrue(all(s == "ALERT" for s in sev[:first_info]))
        self.assertTrue(all(s == "INFO" for s in sev[first_info:]))


if __name__ == "__main__":
    unittest.main()
```

Note: months with zero deals inside the window (e.g. Jul/Sep in single-deal fixtures) legitimately flag too — tests assert only on the months they seed.

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd ~/Desktop/Andrej_Karpathy_Obsidian_FirstRain_Brain
python3 tests/projects/test_execution_coverage.py -v
```

Expected: `ImportError: cannot import name '_compute_pipeline_coverage_by_month'`

- [ ] **Step 3: Implement the function**

In `scripts/projects/build_cashflow_json.py`, insert directly after `_monthly_revenue_from_bigin` returns (after line 1296, before `_build_telegram_briefing`):

```python
# ── Pipeline coverage by EXECUTION month ────────────────────────────────────
# Tracks how loaded each delivery month is (Bigin Project_Month, NOT close
# date). A thin month inside the actionable window fires a briefing flag —
# custom stands need ~6-8 weeks lead time, so by T-10-weeks a thin month is
# a salvage operation, not a prospecting one (spec 2026-07-06).
_COVERAGE_FLOOR_DEFAULT = 4_000_000   # ₹40L; override: CONFIG_EXEC_COVERAGE_FLOOR Notes entry
_COVERAGE_ALERT_WEEKS = 10            # ≤ this many weeks out + thin → ALERT
_COVERAGE_INFO_WEEKS = 18             # ≤ this (≈4 months) + thin → INFO


def _compute_pipeline_coverage_by_month(deals, today, floor=_COVERAGE_FLOOR_DEFAULT):
    """
    Bucket live deals (bucket not in {lost, junk} = won + hot + active) by
    execution month and flag under-filled months vs the floor.

    Returns {floor, dataAvailable, missingExecMonthCount, months, flags}.
    dataAvailable=False (and flags=[]) when NO live deal carries
    project_month — first-run safety: flagging every month as ₹0 before the
    Bigin fetch carries Project_Month would be pure noise.

    Pure function (deals + date in, dict out) — unit-tested in
    tests/projects/test_execution_coverage.py.
    """
    from datetime import date as _date

    live = [d for d in deals if d.get("bucket") not in ("lost", "junk")]
    dated = [d for d in live if d.get("project_month")]
    data_available = len(dated) > 0

    by_month: dict[str, dict] = {}
    for d in dated:
        mk = str(d["project_month"])[:7]  # "YYYY-MM-DD" → "YYYY-MM"
        b = by_month.setdefault(mk, {"value": 0.0, "committed": 0.0,
                                     "active": 0.0, "count": 0, "unpriced": 0})
        amt = float(d.get("amount") or 0)
        b["value"] += amt
        b["count"] += 1
        if amt <= 0:
            b["unpriced"] += 1
        stage_l = (d.get("stage") or "").strip().lower()
        if d.get("bucket") == "won" or stage_l in REVENUE_STAGES:
            b["committed"] += amt
        else:
            b["active"] += amt

    cur_mk = today.strftime("%Y-%m")
    months, flags = [], []
    for mk in _FY_MONTHS:
        if mk < cur_mk:
            continue
        first_day = _date(int(mk[:4]), int(mk[5:7]), 1)
        weeks_out = max(0.0, (first_day - today).days / 7.0)
        b = by_month.get(mk, {"value": 0.0, "committed": 0.0,
                              "active": 0.0, "count": 0, "unpriced": 0})
        severity = "OK"
        if data_available and b["value"] < floor:
            if weeks_out <= _COVERAGE_ALERT_WEEKS:
                severity = "ALERT"
            elif weeks_out <= _COVERAGE_INFO_WEEKS:
                severity = "INFO"
        row = {
            "month": mk,
            "label": first_day.strftime("%b'%y"),
            "value": b["value"],
            "committedValue": b["committed"],
            "activeValue": b["active"],
            "dealCount": b["count"],
            "unpricedCount": b["unpriced"],
            "weeksOut": round(weeks_out, 1),
            "severity": severity,
        }
        months.append(row)
        if severity in ("ALERT", "INFO"):
            flags.append(row)

    flags.sort(key=lambda r: (r["severity"] != "ALERT", r["month"]))
    return {
        "floor": floor,
        "dataAvailable": data_available,
        "missingExecMonthCount": len(live) - len(dated),
        "months": months,
        "flags": flags,
    }
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd ~/Desktop/Andrej_Karpathy_Obsidian_FirstRain_Brain
python3 tests/projects/test_execution_coverage.py -v
```

Expected: `OK` — 11 tests pass.

- [ ] **Step 5: Commit**

```bash
git add scripts/projects/build_cashflow_json.py tests/projects/test_execution_coverage.py
git commit -m "feat(coverage): compute pipeline coverage by execution month

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 3: Wire floor config + call site + JSON key

**Files:**
- Modify: `scripts/projects/build_cashflow_json.py:183-184` (`_load_finance` Notes parsing) and `:1794-1917` (`_compose_cashflow`)

**Interfaces:**
- Consumes: `_compute_pipeline_coverage_by_month` from Task 2; `finance` dict from `_load_finance()`.
- Produces: `finance["execCoverageFloor"]` (float or absent); local `pipeline_coverage_meta` in `_compose_cashflow`; `cashflow["FR"]["pipelineCoverageMeta"]` (the exact key Tasks 4 and 6 read).

- [ ] **Step 1: Parse the floor override in `_load_finance`**

In `scripts/projects/build_cashflow_json.py`, the Notes loop at lines 175-184 currently ends with the `CONFIG_WEEK_ENDING` branch:

```python
            elif cat == "CONFIG_WEEK_ENDING" and val:
                finance["weekEnding"] = val
```

Add a branch after it (same idiom as `CONFIG_MONTHLY_BURN` at lines 178-182):

```python
            elif cat == "CONFIG_EXEC_COVERAGE_FLOOR" and val:
                try:
                    finance["execCoverageFloor"] = float(val.replace(",", "").replace("₹", ""))
                except ValueError:
                    pass
```

- [ ] **Step 2: Compute coverage in `_compose_cashflow` and add the JSON key**

In `_compose_cashflow`, after the `_compute_cashflow(...)` call block (ends line 1809) and before the `return {` at line 1811, add:

```python
    # ── Pipeline coverage by execution month (spec 2026-07-06) ──────────────
    coverage_floor = finance.get("execCoverageFloor") or _COVERAGE_FLOOR_DEFAULT
    pipeline_coverage_meta = _compute_pipeline_coverage_by_month(
        bigin.get("deals", []), datetime.now().date(), floor=coverage_floor
    )
```

Then in the returned `"FR"` dict, after the three cashflow keys (lines 1874-1876):

```python
            # 12-month cash flow projection (computed above)
            "annual": cf_annual,
            "cashflow": cf_months,
            "quarters": cf_quarters,
```

add:

```python
            # Pipeline coverage by execution month (Bigin Project_Month)
            "pipelineCoverageMeta": pipeline_coverage_meta,
```

- [ ] **Step 3: Verify the build still runs and the key appears**

```bash
cd ~/Desktop/Andrej_Karpathy_Obsidian_FirstRain_Brain
python3 scripts/projects/build_cashflow_json.py --from-files \
  && python3 -c "import json; c=json.load(open('data/projects/cashflow.json')); m=c['FR']['pipelineCoverageMeta']; print('dataAvailable:', m['dataAvailable'], '· flags:', len(m['flags']), '· floor:', m['floor'])"
```

Expected: build completes; prints `dataAvailable: False · flags: 0 · floor: 4000000` (the cache has no `project_month` yet — the first-run guard is doing its job; Task 7 backfills).

- [ ] **Step 4: Commit**

```bash
git add scripts/projects/build_cashflow_json.py
git commit -m "feat(coverage): wire coverage meta + CONFIG_EXEC_COVERAGE_FLOOR into cashflow.json

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 4: Briefing section (TDD)

**Files:**
- Modify: `scripts/projects/build_cashflow_json.py:1299-1304` (signature), `:1461-1467` (section insertion), `:1879-1893` (call site)
- Test: `tests/projects/test_execution_coverage.py` (append class)

**Interfaces:**
- Consumes: `pipeline_coverage_meta` dict shape from Task 2; `pipeline_coverage_meta` local from Task 3.
- Produces: `_build_telegram_briefing(..., pipeline_coverage=None)` keyword arg; a `📅 EXECUTION COVERAGE` section in the briefing string (shown on Telegram + dashboard Alerts tab).

- [ ] **Step 1: Write the failing tests**

Append to `tests/projects/test_execution_coverage.py` (before the `if __name__` block):

```python
class TestBriefingSection(unittest.TestCase):
    def _briefing(self, cov):
        from build_cashflow_json import _build_telegram_briefing
        return _build_telegram_briefing(
            op_cash=10_000_000, monthly_burn=1_000_000, treasury=0,
            od_facility=0, od_utilized=0, norm_receivables=[],
            norm_statutory=[], treasury_sweep={}, cf_annual={},
            secure_concentration=0.0, saltwater_concentration=0.0,
            pipeline_coverage=cov,
        )

    def test_flags_render_section(self):
        cov = _compute_pipeline_coverage_by_month(
            [deal("2026-08-20", 1_440_000, "hot", "Price Quote"),
             deal("2026-07-22", 5_975_000, "won", "Closed Won 26-27"),
             deal("2026-09-16", 6_000_000)], TODAY, FLOOR)
        text = self._briefing(cov)
        self.assertIn("EXECUTION COVERAGE", text)
        self.assertIn("Aug'26", text)
        self.assertIn("🔴", text)

    def test_no_flags_no_section(self):
        cov = _compute_pipeline_coverage_by_month(
            [deal(m + "-15", 9_000_000) for m in
             ["2026-07", "2026-08", "2026-09", "2026-10", "2026-11"]],
            TODAY, FLOOR)
        self.assertEqual(cov["flags"], [])
        self.assertNotIn("EXECUTION COVERAGE", self._briefing(cov))

    def test_no_data_shows_warning_not_alerts(self):
        cov = _compute_pipeline_coverage_by_month(
            [{"deal": "no-pm", "amount": 500_000, "bucket": "active",
              "stage": "Design"}], TODAY, FLOOR)
        text = self._briefing(cov)
        self.assertIn("EXECUTION COVERAGE", text)
        self.assertIn("No Project_Month data", text)
        self.assertNotIn("🔴", text.split("EXECUTION COVERAGE")[1])

    def test_none_coverage_is_safe(self):
        # Callers that don't thread coverage through must not crash.
        self.assertNotIn("EXECUTION COVERAGE", self._briefing(None))
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd ~/Desktop/Andrej_Karpathy_Obsidian_FirstRain_Brain
python3 tests/projects/test_execution_coverage.py -v
```

Expected: the 4 new tests FAIL with `TypeError: _build_telegram_briefing() got an unexpected keyword argument 'pipeline_coverage'`.

- [ ] **Step 3: Implement**

(a) Extend the signature at lines 1299-1304:

```python
def _build_telegram_briefing(
    op_cash, monthly_burn, treasury, od_facility, od_utilized,
    norm_receivables, norm_statutory, treasury_sweep, cf_annual,
    secure_concentration, saltwater_concentration, health_score=None,
    norm_projects=None, bank_latest_balance=None, pipeline_coverage=None
) -> str:
```

(b) Insert the section between the Projects YTD block (ends line 1461) and the Health block (starts line 1463 `# ── Health ──`):

```python
    # ── Execution coverage (pipeline by execution month) ────────────────────
    cov = pipeline_coverage or {}
    cov_flags = cov.get("flags", [])
    if cov_flags or (cov and not cov.get("dataAvailable")):
        lines.append("")
        lines.append("📅 EXECUTION COVERAGE")
        if not cov.get("dataAvailable"):
            lines.append("⚠️ No Project_Month data from Bigin yet — coverage unavailable until next sync.")
        for g in cov_flags[:4]:
            icon = "🔴" if g["severity"] == "ALERT" else "🟡"
            tail = "thin, salvage now" if g["severity"] == "ALERT" else "watch"
            unp = f" ({g['unpricedCount']} unpriced)" if g.get("unpricedCount") else ""
            lines.append(
                f"• {icon} {g['label']}: {fmt(g['value'])} booked vs "
                f"{fmt(cov.get('floor', 0))} floor · ~{int(round(g['weeksOut']))}wk out — {tail}{unp}"
            )
        miss = cov.get("missingExecMonthCount", 0)
        if cov.get("dataAvailable") and miss:
            lines.append(f"⚠️ {miss} live deals missing execution month — coverage understated.")
```

(c) Thread it through the call site — in the `"telegramBriefing": _build_telegram_briefing(` call (lines 1879-1893), add after `bank_latest_balance=bank_txn.get("latestBalance"),`:

```python
                pipeline_coverage=pipeline_coverage_meta,
```

- [ ] **Step 4: Run the full test file**

```bash
cd ~/Desktop/Andrej_Karpathy_Obsidian_FirstRain_Brain
python3 tests/projects/test_execution_coverage.py -v
```

Expected: `OK` — 15 tests pass.

- [ ] **Step 5: Commit**

```bash
git add scripts/projects/build_cashflow_json.py tests/projects/test_execution_coverage.py
git commit -m "feat(coverage): execution-coverage section in daily briefing

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 5: `/finance` Step 1 pulls `Project_Month`

**Files:**
- Modify: `.claude/commands/finance.md:27` (COQL) and `:58-72` (normalization mapping)

**Interfaces:**
- Produces: `project_month` key on every normalized deal in `data/projects/bigin_pipeline_raw.json` (ISO date string or null). `classify_pipeline.py` passes unknown keys through untouched — no change needed there.

- [ ] **Step 1: Add `Project_Month` to the COQL SELECT (line 27)**

Change:

```sql
SELECT id, Deal_Name, Account_Name.id, Account_Name.Account_Name, Amount, Closing_Date, Stage, Pipeline, Probability, Created_Time, Modified_Time, Region, Owner.id FROM Pipelines WHERE Pipeline = 'Sales Pipeline 26-27'
```

to:

```sql
SELECT id, Deal_Name, Account_Name.id, Account_Name.Account_Name, Amount, Closing_Date, Project_Month, Stage, Pipeline, Probability, Created_Time, Modified_Time, Region, Owner.id FROM Pipelines WHERE Pipeline = 'Sales Pipeline 26-27'
```

- [ ] **Step 2: Add the field to the normalization mapping**

In the `normalized_deal = {` block (lines 58-72), after `"close": row.get("Closing_Date"),` add:

```python
    "project_month": row.get("Project_Month"),  # execution month (show date) — coverage flag
```

- [ ] **Step 3: Note the quirk**

In the **Known quirks** list (after line 34's Region bullet), add:

```markdown
- If `Project_Month` errors in COQL, retry without it and set `"project_month": None` for all deals — the coverage flag degrades gracefully (`dataAvailable: false`) instead of false-alerting.
```

- [ ] **Step 4: Commit**

```bash
git add .claude/commands/finance.md
git commit -m "feat(coverage): pull Project_Month in /finance Step 1 Bigin fetch

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 6: Dashboard section on the Projects page

**Files:**
- Modify: `dashboards/dashboard-template.html:3568-3570` (insert between the levers footnote and the `DEMOTED` header)

**Interfaces:**
- Consumes: `FR.pipelineCoverageMeta` (Task 3's key; row shape from Task 2). Reuses existing CSS classes `.v7-section-title`, `.v7-demote-note`, `.v11-cm-dist-label`, `.v11-cm-dist`, `.v11-cm-row`, `.v11-cm-label`, `.v11-cm-bar`, `.v11-cm-fill`, `.v11-cm-count` and helpers `fmt()`/`esc()` — zero new CSS.

- [ ] **Step 1: Insert the render block**

At line 3568-3570 the template currently reads:

```js
    pjHtml += '<div class="v8-lever-footnote"><em>Levers are the FY29 plan — static until reviewed. Full bet options in /plan doc.</em></div>';

    /* ════════ DEMOTED ════════ */
```

Insert between them:

```js
    /* ════════ EXECUTION COVERAGE · pipeline by execution month ════════ */
    var cov = FR.pipelineCoverageMeta || {};
    var covMonths = cov.months || [];
    if (covMonths.length || cov.dataAvailable === false) {
      pjHtml += '<div class="v7-section-title">Execution <em>coverage</em> · by project month</div>';
      if (cov.dataAvailable === false) {
        pjHtml += '<div class="v7-demote-note">⚠️ No Project_Month data from Bigin yet — coverage will populate after the next sync.</div>';
      } else {
        if (cov.missingExecMonthCount) {
          pjHtml += '<div class="v7-demote-note">⚠️ ' + cov.missingExecMonthCount + ' live deals missing execution month — coverage understated.</div>';
        }
        var covMax = Math.max(cov.floor || 0, covMonths.reduce(function(m, r){ return Math.max(m, r.value); }, 0)) || 1;
        pjHtml += '<div class="v11-cm-dist-label">Won + confirmed + active by execution month · floor <strong>' + fmt(cov.floor || 0) + '</strong> · 🔴 thin ≤10wk · 🟡 thin ≤4mo</div>';
        pjHtml += '<div class="v11-cm-dist">';
        covMonths.forEach(function(r){
          var color = r.severity === 'ALERT' ? 'var(--red)' : r.severity === 'INFO' ? 'var(--amber)' : 'var(--green)';
          var widthPct = Math.max(2, Math.min(100, r.value / covMax * 100));
          var count = fmt(r.value) + ' · ' + r.dealCount + (r.unpricedCount ? ' (' + r.unpricedCount + ' unpriced)' : '');
          pjHtml += '<div class="v11-cm-row">'
            + '<div class="v11-cm-label">' + esc(r.label) + '</div>'
            + '<div class="v11-cm-bar"><div class="v11-cm-fill" style="width:' + widthPct + '%;background:' + color + '"></div></div>'
            + '<div class="v11-cm-count" style="white-space:nowrap">' + count + '</div>'
            + '</div>';
        });
        pjHtml += '</div>';
      }
    }
```

- [ ] **Step 2: Rebuild and verify the section renders**

```bash
cd ~/Desktop/Andrej_Karpathy_Obsidian_FirstRain_Brain
python3 scripts/projects/build_cashflow_json.py --from-files \
  && grep -c "Execution <em>coverage</em>" dashboards/dashboard.html \
  && grep -c "NaN\|undefined\"" dashboards/dashboard.html || true
```

Expected: build OK; first grep prints `1`; the NaN grep prints `0` (Step-10 validation criterion still holds).

- [ ] **Step 3: Commit**

```bash
git add dashboards/dashboard-template.html
git commit -m "feat(coverage): execution-coverage strip on dashboard Projects page

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 7: Backfill `project_month` + end-to-end verification — ORCHESTRATOR ONLY

**⚠️ This task calls Bigin via MCP. Per the data-pull rule it must be executed by the main Claude session (which has the Bigin MCP), NOT dispatched to a coding subagent. A subagent may do steps 3-5.**

**Files:**
- Rewrite (via MCP + jq/python, following finance.md Step 1): `data/projects/bigin_pipeline_raw.json`
- Regenerate: `data/projects/bigin_pipeline_classified.json`, `data/projects/cashflow.json`, `dashboards/dashboard.html`

**Interfaces:**
- Consumes: the updated Step-1 COQL from Task 5.
- Produces: a live `pipelineCoverageMeta` with `dataAvailable: true`; expected first result — **Aug'26 fires 🔴 ALERT** (₹14.4L booked, ~4wk out).

- [ ] **Step 1: Re-run the Step-1 Bigin fetch with the new COQL** (orchestrator, per finance.md Step 1 — subagent path preferred for the 125-deal dump). Confirm each deal in `data/projects/bigin_pipeline_raw.json` now carries `project_month`.

- [ ] **Step 2: Spot-check the cache**

```bash
cd ~/Desktop/Andrej_Karpathy_Obsidian_FirstRain_Brain
python3 -c "
import json
d = json.load(open('data/projects/bigin_pipeline_raw.json'))['deals']
with_pm = [x for x in d if x.get('project_month')]
print(f'{len(with_pm)}/{len(d)} deals carry project_month')
aug = [x for x in with_pm if str(x['project_month'])[:7]=='2026-08' and x.get('bucket') not in ('lost','junk')]
print('Aug live deals:', [(x['deal'][:40], x['amount']) for x in aug])"
```

Expected: a majority of deals carry `project_month`; Aug live list shows Pharmatech ₹14.4L (bucket key absent in raw — ignore the bucket filter result here if so; the classified file applies it).

- [ ] **Step 3: Classify + rebuild**

```bash
cd ~/Desktop/Andrej_Karpathy_Obsidian_FirstRain_Brain
python3 scripts/projects/classify_pipeline.py \
  && python3 scripts/projects/build_cashflow_json.py --from-files
```

Expected: both complete without error.

- [ ] **Step 4: Verify the flag fired end-to-end**

```bash
cd ~/Desktop/Andrej_Karpathy_Obsidian_FirstRain_Brain
python3 -c "
import json
c = json.load(open('data/projects/cashflow.json'))
m = c['FR']['pipelineCoverageMeta']
assert m['dataAvailable'], 'dataAvailable must be true after backfill'
aug = next(x for x in m['months'] if x['month'] == '2026-08')
print('Aug:', aug['severity'], aug['value'], f\"~{aug['weeksOut']}wk\")
assert aug['severity'] == 'ALERT', 'Aug 2026 must ALERT'
assert 'EXECUTION COVERAGE' in c['FR']['telegramBriefing'], 'briefing section missing'
print('briefing lines:')
[print(' ', l) for l in c['FR']['telegramBriefing'].splitlines() if 'COVERAGE' in l or '🔴' in l or '🟡' in l]"
```

Expected: `Aug: ALERT 1440000 ~3.7wk` (value may differ if Bigin moved), briefing lines print.

- [ ] **Step 5: Run the full project test suite (regression)**

```bash
cd ~/Desktop/Andrej_Karpathy_Obsidian_FirstRain_Brain
for t in tests/projects/test_*.py; do python3 "$t" -q || echo "FAILED: $t"; done
```

Expected: no `FAILED:` lines.

- [ ] **Step 6: Commit the regenerated caches**

```bash
git add data/projects/bigin_pipeline_raw.json data/projects/bigin_pipeline_classified.json data/projects/cashflow.json dashboards/dashboard.html
git commit -m "feat(coverage): backfill Project_Month cache — Aug'26 fires first ALERT

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

- [ ] **Step 7: Rollout note — surface to Niloy, do not act unilaterally**

The 08:00 launchd task runs against the vault working tree, so tomorrow's briefing carries the flag as long as this branch stays checked out. Ask Niloy whether to (a) leave `feat/exec-coverage-flag` checked out overnight, or (b) merge to the branch/main he prefers. Do NOT deploy the dashboard now unless he asks — the daily build deploys it anyway (and if he does ask: `bash scripts/deploy_dashboard.sh`, never raw wrangler).

---

## Self-Review Notes

- **Spec coverage:** Part 1 (fetch) → Task 5+7; Part 2 (compute, floor override, unpriced/missing guards) → Tasks 2-3; Part 3 (briefing) → Task 4; Part 4 (dashboard) → Task 6; testing section → Tasks 2/4/7; rollout → Task 7 Step 7. Spec's "sold-out month" regression pinned in `test_sold_out_month_won_only_does_not_flag`.
- **Type consistency:** key names `pipelineCoverageMeta` / `project_month` / row fields checked across Tasks 2→3→4→6.
- **Deviation from spec, intentional:** the dashboard has no separate "Pipeline" tab — pipeline renders on the Projects page (`page-projects`), so the coverage strip lives there (spec said "Pipeline tab"; same surface in practice).
