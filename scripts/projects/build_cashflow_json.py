"""
build_cashflow_json.py
=======================
Orchestrator. Runs all sub-modules in order, composes cashflow.json
matching the v11 renderer's expected schema, substitutes into
dashboard-template.html, writes dashboard.html.

This is the entrypoint invoked by /finance at 08:00 IST daily.

Order of operations:
    1. fetch_bigin_pipeline  → bigin_pipeline_raw.json
    2. classify_pipeline     → bigin_pipeline_classified.json
    3. read_sheet_projects   → sheet_projects.json
    4. compute_momentum      → momentum.json + appends snapshot
    5. drift_check           → drift_report.json
    6. build_cashflow_json   → cashflow.json + dashboard.html

Usage:
    python build_cashflow_json.py
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# Add scripts/projects to path so sub-module imports work
sys.path.insert(0, str(Path(__file__).parent))

from fetch_bigin_pipeline import fetch_pipeline
from classify_pipeline import classify, _match_industry
from read_sheet_projects import read_sheet
from compute_momentum import compute as compute_momentum
from drift_check import check as drift_check


TEMPLATE_PATH = Path("dashboards/dashboard-template.html")
OUTPUT_HTML = Path("dashboards/dashboard.html")
CASHFLOW_JSON = Path("data/projects/cashflow.json")
# New per-tab sheet files (written by read_cashflow_xlsx.py)
CASH_POSITION_JSON = Path("data/projects/sheet_cash_position.json")
RECEIVABLES_JSON = Path("data/projects/sheet_receivables.json")
PAYABLES_JSON = Path("data/projects/sheet_payables.json")
STATUTORY_JSON = Path("data/projects/sheet_statutory.json")
NOTES_JSON = Path("data/projects/sheet_notes.json")
# Legacy fallback (written by old /finance flow — kept for backward compat)
FINANCE_JSON = Path("data/projects/sheet_finance.json")

EXEC_NAMES = {"CK": "Chinmay", "SP": "Shilpa", "DS": "Dhruv", "ND": "Niloy"}

IMESSAGE_TXN_JSON = Path("data/projects/_cache/hdfc_imessages.json")


def build():
    print("=" * 60)
    print(f"/finance Projects tab build · {datetime.now().astimezone().isoformat()}")
    print("=" * 60)

    # Step 1: Bigin pipeline
    bigin_raw = fetch_pipeline()

    # Step 2: classify
    bigin_classified = classify(bigin_raw)

    # Step 3: Sheet
    sheet = read_sheet()

    # Step 4: momentum
    momentum = compute_momentum(bigin_classified)

    # Step 5: drift
    drift = drift_check(bigin_classified, sheet)

    # Step 6: load iMessage SMS data FIRST so OD override happens inside _compose_cashflow
    imessage_data = _load_imessage_txns()

    # Step 7: compose cashflow.json matching v11 renderer schema
    cashflow = _compose_cashflow(bigin_classified, sheet, momentum, drift, imessage_data=imessage_data)

    # Attach iMessage data to cashflow (for dashboard Data tab + downstream use)
    cashflow["imessageBankData"] = imessage_data
    # Surface SMS-feed health at top level so the dashboard can badge a dead feed.
    _imsg_meta = cashflow["imessageBankData"].get("meta", {})
    cashflow["smsFeedStatus"] = _imsg_meta.get("feed_status", "unknown")
    cashflow["smsFeedHealth"] = _imsg_meta.get("feed_health", {})
    if cashflow["smsFeedStatus"] == "stale":
        fh = cashflow["smsFeedHealth"]
        print(f"  📵 HDFC SMS feed STALE — newest chat.db msg {fh.get('hours_since_any')}h old. "
              f"iPhone->Mac sync likely down; relying on Gmail HDFC email alerts.")
    sms_only = [
        t for t in cashflow["imessageBankData"].get("transactions", [])
        if t.get("confidence") == "sms_only" and t.get("type") == "credit"
    ]
    if sms_only:
        print(f"  ⚠  {len(sms_only)} SMS-only credit(s) not yet in Gmail:")
        for t in sms_only:
            src = " [MANUAL]" if t.get("source") == "manual_paste" else ""
            print(f"     {t['date'][:16]}  ₹{t['amount']:,.0f}  acc:{t['account']}  {t.get('counterparty','?')}{src}")

    CASHFLOW_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(CASHFLOW_JSON, "w") as f:
        json.dump(cashflow, f, indent=2, default=str)

    # Render dashboard
    _render_dashboard(cashflow)

    print("=" * 60)
    print(f"✓ Dashboard rendered → {OUTPUT_HTML}")
    print(f"  drift: {drift['counts']['ALERT']} ALERT · {drift['counts']['WARNING']} WARNING")
    print(f"  momentum: {momentum['mode']} ({momentum['snapshot_count']} snapshots)")
    print("=" * 60)


def _load_finance():
    """
    Load financial data from the per-tab sheet JSON files written by
    read_cashflow_xlsx.py.  Falls back to the legacy sheet_finance.json
    for any tab that is missing (backward compat).
    """
    # --- legacy fallback base ---
    if FINANCE_JSON.exists():
        legacy = json.loads(FINANCE_JSON.read_text())
    else:
        legacy = {}

    finance = {
        "cash": legacy.get("cash", {}),
        "receivables": legacy.get("receivables", []),
        "payables": legacy.get("payables", []),
        "statutory": legacy.get("statutory", []),
        "weekEnding": legacy.get("weekEnding"),
        "monthlyBurn": None,
    }

    # --- Cash_Position (new) ---
    if CASH_POSITION_JSON.exists():
        cp = json.loads(CASH_POSITION_JSON.read_text())
        # "cash" is None when the tab is empty; keep legacy if so
        if cp.get("cash") is not None:
            finance["cash"] = cp["cash"]
        finance["_cash_alerts"] = cp.get("alerts", [])

    # --- Receivables (new) ---
    if RECEIVABLES_JSON.exists():
        rv = json.loads(RECEIVABLES_JSON.read_text())
        all_recv = rv.get("receivables", [])
        # Suppress rows where balance = 0 — fully paid invoices that the sheet
        # still marks as "Open". These have nothing to chase and create false
        # overdue alerts. Sonal's sheet is the permanent fix; this filter
        # prevents noise until she marks them Closed.
        finance["receivables"] = [
            r for r in all_recv
            if float(r.get("balance", r.get("amount", 0)) or 0) > 0
        ]

    # --- Payables (new) ---
    if PAYABLES_JSON.exists():
        pv = json.loads(PAYABLES_JSON.read_text())
        all_pay = pv.get("payables", [])
        # Suppress paid rows (balance = 0) — same as receivables filter.
        finance["payables"] = [
            p for p in all_pay
            if float(p.get("balance", p.get("amount", 0)) or 0) > 0
        ]

    # --- Statutory (new) ---
    if STATUTORY_JSON.exists():
        st = json.loads(STATUTORY_JSON.read_text())
        finance["statutory"] = st.get("obligations", [])

    # --- Notes: CONFIG entries + monthly revenue/burn overrides ---
    if NOTES_JSON.exists():
        notes = json.loads(NOTES_JSON.read_text())
        for entry in notes.get("entries", []):
            cat = (entry.get("category") or "").strip().upper()
            val = (entry.get("entry") or "").strip()
            if cat == "CONFIG_MONTHLY_BURN" and val:
                try:
                    finance["monthlyBurn"] = float(val.replace(",", "").replace("₹", ""))
                except ValueError:
                    pass
            elif cat == "CONFIG_WEEK_ENDING" and val:
                finance["weekEnding"] = val
            elif cat == "CONFIG_EXEC_COVERAGE_FLOOR" and val:
                try:
                    finance["execCoverageFloor"] = float(val.replace(",", "").replace("₹", ""))
                except ValueError:
                    pass
        # Monthly revenue overrides (Notes wins over Bigin for that month)
        finance["notesMonthlyRevenue"] = notes.get("monthlyRevenue", {})
        # Per-month burn overrides: CONFIG_MONTHLY_BURN_YYYY-MM rows
        finance["notesMonthlyBurn"] = notes.get("monthlyBurn", {})

    return finance


def _load_imessage_txns():
    """
    Load iMessage-sourced HDFC transactions written by parse_hdfc_imessages.py.
    Returns the full JSON dict (or an empty scaffold if the file doesn't exist yet).
    """
    if not IMESSAGE_TXN_JSON.exists():
        return {"meta": {"source": "imessage_sms", "transaction_count": 0, "note": "file not found"}, "transactions": []}
    try:
        return json.loads(IMESSAGE_TXN_JSON.read_text())
    except Exception as e:
        return {"meta": {"source": "imessage_sms", "transaction_count": 0, "error": str(e)}, "transactions": []}


def _compute_derived(bigin, sheet, finance):
    """Compute fields the renderer needs that aren't in any source file."""
    deals = bigin.get("deals", [])
    projects = sheet.get("projects", [])

    # Region / industry catalogs for filter dropdowns (expand short codes to full names)
    raw_regions = ({d.get("region") for d in deals if d.get("region")} |
                   {p.get("region") for p in projects if p.get("region")})
    all_regions = sorted({_REGION_NAME_MAP.get(r, r) for r in raw_regions} - {"Unknown"})
    all_industries = sorted({d.get("industry") for d in deals if d.get("industry")})

    # Pipeline totals by account for concentration
    account_totals = {}
    pipeline_total = 0.0
    saltwater_total = 0.0
    for d in deals:
        amt = float(d.get("amount") or 0)
        pipeline_total += amt
        name = d.get("account_name") or ""
        account_totals[name] = account_totals.get(name, 0.0) + amt
        if d.get("region") and d["region"].lower() not in ("india", "in"):
            saltwater_total += amt

    secure_pct = 0.0
    if pipeline_total > 0:
        secure_pct = account_totals.get("Secure Meters Pvt Ltd", 0.0) / pipeline_total

    saltwater_pct = (saltwater_total / pipeline_total) if pipeline_total > 0 else 0.0

    # Total receivables outstanding from Secure/international
    receivables = finance.get("receivables", [])
    saltwater_outstanding = sum(
        # new format uses "balance"; legacy format used "amount"
        r.get("balance", r.get("amount", 0)) for r in receivables
        if "vitafoods" in r.get("client", "").lower() or "international" in r.get("client", "").lower()
    )

    # Top actions — derive from drift ALERTs + upcoming receivables
    top_actions = []
    today = datetime.now().date()
    for r in receivables:
        bal = r.get("balance", r.get("amount", 0))
        try:
            due = datetime.fromisoformat(r["dueDate"]).date()
            overdue = (today - due).days
        except Exception:
            overdue = -999
        if overdue > 0:
            top_actions.append({"icon": "🔴", "text": f"Chase {r['client']} · ₹{bal:,} · {overdue}d overdue"})
        elif overdue >= -7:
            top_actions.append({"icon": "🟠", "text": f"Confirm {r['client']} payment · ₹{bal:,} · due {r['dueDate']}"})

    # Payables: pending within 7 days or overdue
    # New format: daysToDue / balance / vendor. Legacy format: daysLeft / amount.
    payables = finance.get("payables", [])
    if isinstance(payables, list):
        for p in payables:
            if p.get("status") == "paid":
                continue
            days_left = p.get("daysToDue", p.get("daysLeft"))
            amt = p.get("balance", p.get("amount", 0))
            vendor = p.get("vendor", "")
            if days_left is None:
                continue
            if days_left < 0:
                top_actions.append({"icon": "🔴", "text": f"Pay {vendor} · ₹{amt:,.0f} · {abs(days_left)}d overdue"})
            elif days_left <= 7:
                top_actions.append({"icon": "🟠", "text": f"Pay {vendor} · ₹{amt:,.0f} · due in {days_left}d"})

    # Cash critical flag — monthlyBurn lives on finance (CONFIG_MONTHLY_BURN Notes entry)
    cash = finance.get("cash", {}) or {}
    op_cash = cash.get("operatingCash", 0)
    burn = finance.get("monthlyBurn") or cash.get("monthlyBurn") or 0
    runway = (op_cash / burn) if burn > 0 else 0
    if burn > 0 and runway < 2:
        top_actions.insert(0, {"icon": "🔴", "text": f"Cash critical · {runway:.1f}mo runway · activate OD or sweep treasury"})

    return {
        "allRegions": all_regions,
        "allIndustries": all_industries,
        "secureConcentration": secure_pct,
        "secureRevenue": account_totals.get("Secure Meters Pvt Ltd", 0.0),
        "pipelineTotal": pipeline_total,
        "saltwaterConcentration": saltwater_pct,
        "saltwaterOutstanding": saltwater_outstanding,
        "topActions": top_actions,
    }


BANK_TXN_JSON = Path("data/projects/sheet_bank_transactions.json")
TREASURY_JSON = Path("data/projects/sheet_treasury.json")

# ── Field-name normalization ────────────────────────────────────────────────
# The dashboard template JS uses old field names; our xlsx parser uses new ones.
# We add aliases here so the template renders correctly without editing JS.

# Region short codes from classify_pipeline.py → full names expected by regionColors in template.
_REGION_NAME_MAP = {
    "SEA": "South East Asia",
    "ME":  "Middle East",
    "ROW": "Rest of the World",
    "RoW": "Rest of the World",  # legacy alias
}

# Payable flexibility values from the sheet → CSS class names the template expects.
_FLEX_MAP = {
    "flexible":          "can-delay-30d",
    "can-delay-7d":      "can-delay-7d",
    "can-delay-30d":     "can-delay-30d",
    "can-delay-45d":     "can-delay-45d",
    "can-delay-60d":     "can-delay-60d",
    "can-delay-90d":     "can-delay-90d",
    "negotiate":         "can-delay-7d",
    "negotiable":        "can-delay-7d",
    "inflexible":        "must-pay",
    "rigid":             "must-pay",   # sheet dropdown alias
    "must-pay":          "must-pay",
    "must pay":          "must-pay",
    "fixed":             "must-pay",
    "statutory":         "must-pay",
}


def _normalize_receivable(r: dict) -> dict:
    """Add JS-expected field aliases to receivable dict."""
    out = dict(r)
    # daysOD alias (template reads daysOD; parser writes daysOverdue)
    if "daysOD" not in out:
        out["daysOD"] = out.get("daysOverdue", 0) or 0
    # invoice alias (template reads r.invoice; parser writes r.invoiceNo)
    if "invoice" not in out:
        out["invoice"] = out.get("invoiceNo", out.get("invoiceRef", "")) or ""
    # exec alias (template reads r.exec; parser writes r.execOwner)
    if "exec" not in out:
        out["exec"] = out.get("execOwner", "") or ""
    # collectionStatus — human-readable collection action label for the right column
    # Derived from daysOD + priority; overrides the raw financial status "Open/Paid"
    days_od = out["daysOD"]
    priority = (out.get("priority") or "").lower()
    last_contact = (out.get("lastContactType") or "").strip()
    if days_od > 30:
        out["collectionStatus"] = "ESCALATE"
    elif days_od > 7:
        out["collectionStatus"] = "CHASING"
    elif days_od > 0:
        out["collectionStatus"] = "CHASING" if last_contact else "PENDING"
    elif priority in ("high", "urgent"):
        out["collectionStatus"] = "PENDING"
    else:
        out["collectionStatus"] = "NEW"
    return out


def _normalize_statutory(s: dict) -> dict:
    """Add JS-expected field aliases to statutory obligation dict."""
    out = dict(s)
    # amount (template) ← amountPayable (xlsx parser)
    if "amount" not in out:
        out["amount"] = out.get("amountPayable", 0) or 0
    # daysLeft (template) ← daysToDue (xlsx parser)
    if "daysLeft" not in out:
        dtd = out.get("daysToDue")
        out["daysLeft"] = int(dtd) if dtd is not None else -999
    # due (template) ← dueDate (xlsx parser)
    if "due" not in out:
        out["due"] = out.get("dueDate", "") or ""
    # name (template) ← obligationType (xlsx parser)
    if "name" not in out:
        out["name"] = out.get("obligationType", "") or ""
    # type (template sub-label) ← obligationType
    if "type" not in out:
        out["type"] = out.get("obligationType", "") or ""
    return out


def _normalize_payable(p: dict) -> dict:
    """Add field aliases the JS template expects from the old data format."""
    out = dict(p)
    # amount (template) ← balance (xlsx parser)
    if "amount" not in out:
        out["amount"] = out.get("balance", 0) or 0
    # daysLeft (template) ← daysToDue (xlsx parser).  Negative = overdue.
    if "daysLeft" not in out:
        dtd = out.get("daysToDue")
        out["daysLeft"] = int(dtd) if dtd is not None else -999
    # due (template) ← dueDate (xlsx parser)
    if "due" not in out:
        out["due"] = out.get("dueDate", "") or ""
    # invoice (template) ← invoiceNo (xlsx parser)
    if "invoice" not in out:
        out["invoice"] = out.get("invoiceNo", out.get("invoiceRef", "")) or ""
    # Normalise flexibility to the 3 CSS class values the template expects
    flex_raw = (out.get("flexibility") or "can-delay-7d").lower().strip()
    out["flexibility"] = _FLEX_MAP.get(flex_raw, "can-delay-7d")
    return out


def _normalize_project(p: dict) -> dict:
    """Add JS-expected field aliases to a project dict from sheet_projects.json."""
    out = dict(p)
    # sales (template) ← sales_sp (xlsx parser)
    if "sales" not in out:
        out["sales"] = out.get("sales_sp", 0) or 0
    # variableCost (template) ← variable_cost_cp (xlsx parser)
    if "variableCost" not in out:
        out["variableCost"] = out.get("variable_cost_cp", 0) or 0
    # isRepeat (template) ← is_repeat (xlsx parser)
    if "isRepeat" not in out:
        out["isRepeat"] = out.get("is_repeat", False)
    # contributionPct: xlsx parser stores as decimal (0.38); template expects percent (38.0)
    raw_pct = out.get("contributionPct", 0) or 0
    if raw_pct <= 1.0:
        out["contributionPct"] = round(raw_pct * 100, 1)
    # industry: not in Projects sheet — infer from company + project name via regex
    if not out.get("industry") or out.get("industry") == "Unknown":
        out["industry"] = _match_industry(f"{out.get('company', '')} {out.get('project', '')}")
    # Normalize region short codes
    out["region"] = _REGION_NAME_MAP.get(out.get("region", ""), out.get("region", "Unknown"))
    return out


def _normalize_deal(d: dict) -> dict:
    """Normalize a Bigin pipeline deal: expand region short codes."""
    out = dict(d)
    out["region"] = _REGION_NAME_MAP.get(out.get("region", ""), out.get("region", "Unknown"))
    return out


# ── Treasury Sweep computation ──────────────────────────────────────────────

def _derive_od_from_sms(imessage_data: dict) -> "dict | None":
    """
    Extract the most recent OD position from iMessage SMS data.

    HDFC SMS alerts for account 0241 include 'Avl bal:INR -X' which encodes
    the OD balance directly. A negative available balance = OD drawn.

    Returns a dict:
        {odUtilized, operatingCash, date, source, rawBalance}
    or None if no 0241 Avl-bal snapshot is available.

    The caller should compare `date` against `sheet_cash_position.json`'s
    `cash.date` and use whichever is more recent as the authoritative value.
    """
    snapshots = (imessage_data or {}).get('od_balance_snapshots', [])
    if not snapshots:
        return None
    # Already sorted most-recent-first by the parser
    latest = snapshots[0]
    raw_balance = latest['balance']
    od_utilized = latest['odUtilized']
    # operatingCash = -odUtilized (conservative: assumes CA net position is
    # effectively funded by OD, same convention as Sonal's manual entries)
    return {
        'odUtilized': od_utilized,
        'operatingCash': -od_utilized,
        'date': latest['date'][:10],   # YYYY-MM-DD
        'source': 'hdfc_sms',
        'rawBalance': raw_balance,
    }


def _reconcile_bank_balance(bank_txn: Optional[dict]) -> dict:
    """Compare the running balance (latest snapshot + activity since) against
    the freshest embedded "Available Balance" line.

    Returns a dict with `status` (ok / drift / material_gap / no_data),
    `delta_inr`, `latest_anchor_date`, `latest_embedded_date`, and a
    human-readable `note`. Drift > Rs 1L is flagged material_gap and surfaces
    in the dashboard + Telegram so silent cache drift can't compound.
    """
    if not bank_txn:
        return {"status": "no_data", "delta_inr": 0, "note": "no bank txn data"}

    txns = bank_txn.get("transactions", []) or []
    snap = bank_txn.get("latestBalance") or {}
    if not snap or "amount" not in snap or "date" not in snap:
        return {"status": "no_data", "delta_inr": 0, "note": "no balance snapshot found"}

    anchor_amt = float(snap["amount"])
    anchor_date = str(snap["date"])
    anchor_acct = str(snap.get("account") or "")

    # Sum credits - debits for same account AFTER snapshot date.
    net = 0.0
    embedded = None
    embedded_date = None
    for t in sorted(txns, key=lambda x: str(x.get("date", ""))):
        if str(t.get("account") or "") != anchor_acct:
            continue
        d = str(t.get("date") or "")
        if d > anchor_date and t.get("direction") in ("credit", "debit"):
            net += float(t.get("amount") or 0) * (1 if t["direction"] == "credit" else -1)
        # Track latest embedded balance for the SAME account
        if t.get("_embeddedBalance") is not None and d >= (embedded_date or ""):
            embedded = float(t["_embeddedBalance"])
            embedded_date = d

    computed = anchor_amt + net

    if embedded is None:
        return {
            "status": "no_embedded",
            "delta_inr": 0,
            "anchor_date": anchor_date,
            "computed_balance": computed,
            "note": "no embedded 'Available Balance' line in any recent txn email — reconciliation skipped",
        }

    delta = computed - embedded
    abs_delta = abs(delta)
    if abs_delta < 10_000:
        status = "ok"
    elif abs_delta < 100_000:
        status = "drift"
    else:
        status = "material_gap"

    return {
        "status": status,
        "delta_inr": round(delta, 2),
        "computed_balance": round(computed, 2),
        "embedded_balance": round(embedded, 2),
        "anchor_date": anchor_date,
        "embedded_date": embedded_date,
        "note": (
            f"Computed Rs {computed:,.0f} vs HDFC-embedded Rs {embedded:,.0f} "
            f"(Δ Rs {delta:+,.0f}) — anchor {anchor_date}, latest body {embedded_date}"
        ),
    }


def _compute_sweep(op_cash: float, monthly_burn: float,
                   od_facility: float, od_utilized: float,
                   receivables: list = None, payables: list = None) -> tuple[dict, dict]:
    """
    Returns (sweepConfig, treasurySweep) dicts for the dashboard Overview card.

    Phase-aware float target (salary hits in week 1 of every month):
      Days  1–7  (post-salary):  1.0× burn  — salary already out, lower float needed
      Days  8–20 (mid-month):    1.5× burn  — standard operating window
      Days 21–31 (pre-salary):   2.0× burn  — pre-fund next salary cycle

    Net cash position = op_cash + expected_inflows_30d − expected_outflows_30d
    OD draw recommendation is against net position, not raw operating cash.
    Treasury is never touched while OD headroom remains.
    """
    from datetime import date as _date
    import calendar as _calendar

    today = _date.today()
    day = today.day
    min_sweep = 200_000  # ignore tiny movements

    def _fmt(n):
        abs_n = abs(n)
        sign = "-" if n < 0 else ""
        if abs_n >= 10_00_000:
            return f"{sign}₹{abs_n/1_00_000:.1f}L"
        if abs_n >= 1_000:
            return f"{sign}₹{abs_n/1_000:.0f}K"
        return f"{sign}₹{int(abs_n)}"

    # ── Phase logic ──────────────────────────────────────────────────────────
    if day <= 7:
        phase = "post-salary"
        float_multiplier = 1.0
        phase_note = (
            f"Day {day}: salary week just cleared — lower float buffer applies (1.0× burn). "
            "Major cash out already happened; focus on receivables chase."
        )
    elif day <= 20:
        phase = "mid-month"
        float_multiplier = 1.5
        phase_note = (
            f"Day {day}: mid-month window — standard float buffer applies (1.5× burn). "
            "No salary pressure for ~{} days.".format(
                (1 + _calendar.monthrange(today.year, today.month)[1] - day) % 31 + 7
            )
        )
    else:
        phase = "pre-salary"
        float_multiplier = 2.0
        days_to_salary = (_calendar.monthrange(today.year, today.month)[1] - day) + 7
        phase_note = (
            f"Day {day}: pre-salary phase — elevated float buffer (2.0× burn). "
            f"Next salary ~{days_to_salary}d away. Build cash now."
        )

    float_target = monthly_burn * float_multiplier
    od_available = od_facility - od_utilized

    config = {
        "workingFloatTarget": float_target,
        "workingFloatMultiplier": float_multiplier,
        "phase": phase,
        "dayOfMonth": day,
        "minSweepSize": min_sweep,
        "cadence": "daily",
    }

    if monthly_burn <= 0:
        sweep = {
            "direction": "AT_TARGET",
            "verdict": "Hold — monthly burn not configured",
            "rationale": "Set CONFIG_MONTHLY_BURN in the Notes tab to enable sweep intelligence.",
            "recommendedAmount": 0,
            "confidence": "LOW",
            "nextReview": "after Notes update",
        }
        return config, sweep

    # ── Net cash position (30-day horizon) ───────────────────────────────────
    recv_list = receivables or []
    pay_list  = payables  or []

    # Expected inflows: receivables due within 30d (daysLeft <= 30, or already overdue)
    # Use balance field; exclude rent/non-project (vendor field check)
    expected_inflows = sum(
        float(r.get("balance", r.get("amount", 0)) or 0)
        for r in recv_list
        if (r.get("daysLeft", r.get("daysOD", 0)) or 0) <= 30
    )

    # Expected outflows: payables due within 30d (daysLeft <= 30, negative daysLeft = overdue)
    # Flag salary payables separately (vendor name contains "salary" / "payroll" / "staff")
    salary_due_30d = 0.0
    vendor_due_30d = 0.0
    salary_keywords = {"salary", "payroll", "staff", "wages", "remuneration"}
    for p in pay_list:
        days_left = float(p.get("daysLeft", p.get("daysToDue", 999)) or 999)
        amt = float(p.get("amount", p.get("balance", 0)) or 0)
        vendor = (p.get("vendor", p.get("vendorName", "")) or "").lower()
        if days_left <= 30:
            if any(kw in vendor for kw in salary_keywords):
                salary_due_30d += amt
            else:
                vendor_due_30d += amt

    expected_outflows = salary_due_30d + vendor_due_30d

    # Net 30d position
    net_position_30d = op_cash + expected_inflows - expected_outflows
    net_deficit      = float_target - net_position_30d   # positive = need cash
    raw_deficit      = float_target - op_cash            # cash-only view

    # Use net position as primary for DEFICIT checks (when we need to draw OD
    # or sweep treasury inward, future inflows matter — they tell us whether
    # the shortfall is bridged by tomorrow's receivables).
    has_flow_data = bool(recv_list or pay_list)
    working_deficit = net_deficit if has_flow_data else raw_deficit

    # SURPLUS check is different: we can only deploy CASH ON HAND today.
    # A 30d-projected surplus driven by expected receivables is not deployable
    # — collecting those receivables takes weeks and the MF deployment must
    # come from money already in the bank. Cap deployable surplus by today's
    # cash above float so we never recommend deploying funds that aren't there.
    # (Fix 17-Jun-2026: prior code used -working_deficit which sourced
    # ~₹84L of "surplus" from ₹142L of expected receivables while op_cash
    # was below float — would have left 0247 deeply negative on execution.)
    today_surplus    = max(0.0, op_cash - float_target)
    horizon_surplus  = max(0.0, net_position_30d - float_target)
    surplus          = min(today_surplus, horizon_surplus)

    # ── Build context lines for rationale ────────────────────────────────────
    flow_context = ""
    if has_flow_data:
        flow_context = (
            f" Net 30d position: {_fmt(net_position_30d)} "
            f"(+{_fmt(expected_inflows)} receivables − {_fmt(expected_outflows)} payables"
            + (f", incl. {_fmt(salary_due_30d)} salary" if salary_due_30d > 0 else "")
            + ")."
        )

    # ── Sweep decision ────────────────────────────────────────────────────────
    if surplus > min_sweep:
        amount = surplus
        if od_utilized > min_sweep:
            # OD is active — repaying OD (12.5% p.a.) saves more than MF yields (7% p.a.).
            # Collect receivables → repay OD first, then deploy any remaining surplus to MF.
            od_repay = min(od_utilized, amount)
            mf_deploy = max(0.0, amount - od_utilized)
            monthly_od_saving = od_repay * 0.125 / 12
            if mf_deploy > min_sweep:
                verdict = f"Repay OD {_fmt(od_repay)} first, then deploy {_fmt(mf_deploy)} to liquid MF"
                howto = (
                    "Step 1: Collect receivables → transfer to HDFC 0247 → reduce OD 0241 by "
                    f"{_fmt(od_repay)} (saves ₹{monthly_od_saving:,.0f}/mo at 12.5% p.a.). "
                    f"Step 2: Deploy remaining {_fmt(mf_deploy)} to HDFC Liquid Fund – Growth. "
                    "Update Notes tab: SWEEP_EXECUTED YYYY-MM-DD."
                )
            else:
                verdict = f"Repay OD {_fmt(od_repay)} — do not deploy to MF until OD cleared"
                howto = (
                    "Collect receivables → transfer to HDFC 0247 → reduce OD 0241. "
                    f"Saves ₹{monthly_od_saving:,.0f}/mo at 12.5% p.a. MF deployment deferred until OD = 0."
                )
            sweep = {
                "direction": "REPAY_OD",
                "verdict": verdict,
                "headline": f"OD {_fmt(od_utilized)} active — repay before deploying to MF (12.5% > 7%)",
                "rationale": (
                    f"{phase_note} Operating cash {_fmt(op_cash)} · float target {_fmt(float_target)} "
                    f"({float_multiplier}× burn).{flow_context} "
                    f"Net surplus {_fmt(amount)} on 30d horizon, but OD {_fmt(od_utilized)} is being "
                    f"drawn at 12.5% p.a. — 5.5 pts more expensive than 7% MF yield. "
                    f"Repaying OD saves {_fmt(monthly_od_saving)}/mo. Chase receivables first."
                ),
                "recommendedAmount": od_repay,
                "destination": "Repay HDFC OD 0241",
                "mfDeploy": mf_deploy,
                "annualODSaving": round(od_repay * 0.125),
                "actionFor": "Niloy",
                "howTo": howto,
                "confidence": "HIGH",
                "nextReview": "today before 17:00",
                "phase": phase,
            }
        else:
            sweep = {
                "direction": "OUTWARD",
                "verdict": f"Deploy {_fmt(amount)} to liquid MF",
                "headline": f"{_fmt(amount)} above working float — invest the surplus",
                "rationale": (
                    f"{phase_note} Operating cash {_fmt(op_cash)} · float target {_fmt(float_target)} "
                    f"({float_multiplier}× burn).{flow_context} "
                    f"Surplus {_fmt(amount)} — deploy to HDFC Liquid Fund at ~7% p.a."
                ),
                "recommendedAmount": amount,
                "destination": "HDFC Liquid Fund – Growth",
                "annualYieldGain": round(amount * 0.07),
                "actionFor": "Sonal",
                "howTo": (
                    "HDFC NetBanking → Mutual Funds → Invest → HDFC Liquid Fund – Growth. "
                    "Enter the amount and confirm. Update Notes tab: SWEEP_EXECUTED YYYY-MM-DD."
                ),
                "confidence": "HIGH",
                "nextReview": "tomorrow 08:00",
                "phase": phase,
            }
    elif working_deficit > min_sweep:
        deficit = working_deficit
        if od_available >= deficit:
            verdict = f"Draw OD {_fmt(deficit)} — do not touch treasury"
            rationale = (
                f"{phase_note} Operating cash {_fmt(op_cash)} · float target {_fmt(float_target)} "
                f"({float_multiplier}× burn).{flow_context} "
                f"Shortfall {_fmt(deficit)} — OD has {_fmt(od_available)} at ~12.5% p.a. "
                "Draw OD first — cheaper than breaking treasury MF compounding."
            )
            how_to = (
                "HDFC NetBanking → Accounts → Current → Draw OD. "
                "Enter exact amount. Notify Sonal. Repay immediately when receivables clear."
            )
            confidence = "HIGH"
        else:
            verdict = f"Redeem {_fmt(deficit)} from liquid MF (OD insufficient)"
            rationale = (
                f"{phase_note} Operating cash {_fmt(op_cash)} · float target {_fmt(float_target)}.{flow_context} "
                f"OD headroom {_fmt(od_available)} insufficient for full deficit {_fmt(deficit)}. "
                "Redeem liquid MF portion of treasury — do NOT touch debt or equity funds."
            )
            how_to = (
                "HDFC NetBanking → Mutual Funds → Redeem → HDFC Liquid Fund. "
                "Redeem exactly the deficit amount. Confirm with Niloy first."
            )
            confidence = "MEDIUM"
        sweep = {
            "direction": "INWARD",
            "verdict": verdict,
            "headline": f"{_fmt(deficit)} shortfall vs {float_multiplier}× burn target — replenish now",
            "rationale": rationale,
            "recommendedAmount": deficit,
            "howTo": how_to,
            "confidence": confidence,
            "nextReview": "today before 17:00",
            "phase": phase,
            "salaryDue30d": salary_due_30d,
            "vendorDue30d": vendor_due_30d,
            "expectedInflows30d": expected_inflows,
            "netPosition30d": net_position_30d,
        }
    elif horizon_surplus > min_sweep and today_surplus < min_sweep:
        # 30d projection looks healthy but cash on hand is below float — the
        # surplus is sitting in unrealised receivables. Tell Niloy to chase
        # collections, not to deploy a sum that isn't there yet.
        sweep = {
            "direction": "HOLD_PENDING_COLLECTION",
            "verdict": (
                f"Hold — 30d position +{_fmt(horizon_surplus)} above float, "
                f"but op_cash {_fmt(op_cash)} is below {_fmt(float_target)}"
            ),
            "headline": "Collect receivables before deploying surplus",
            "rationale": (
                f"{phase_note} Cash {_fmt(op_cash)} · target {_fmt(float_target)}.{flow_context} "
                f"Net 30d projection shows +{_fmt(horizon_surplus)} above float, but those "
                f"funds are still in receivables ({_fmt(expected_inflows)} expected). "
                "Deploying to MF today would push the operating account negative. "
                "Re-evaluate once Sonal posts the next collection cycle."
            ),
            "recommendedAmount": 0,
            "horizonSurplus": horizon_surplus,
            "actionFor": "Chinmay (chase) + Sonal (post collections)",
            "howTo": (
                "Step 1: Chinmay accelerates the next-due receivable (see Collect tab). "
                "Step 2: Once cash arrives in 0247 and op_cash > float_target + Rs 2L, "
                "the next sync will flip this to a deploy recommendation."
            ),
            "confidence": "HIGH",
            "nextReview": "tomorrow 08:00",
            "phase": phase,
        }
    else:
        sweep = {
            "direction": "AT_TARGET",
            "verdict": "Hold — net cash position at target float",
            "headline": "Operating cash within working float range",
            "rationale": (
                f"{phase_note} Cash {_fmt(op_cash)} · target {_fmt(float_target)} "
                f"({float_multiplier}× burn).{flow_context} No sweep needed today."
            ),
            "recommendedAmount": 0,
            "confidence": "HIGH",
            "nextReview": "tomorrow 08:00",
            "phase": phase,
        }

    return config, sweep


# ── Levers computation ──────────────────────────────────────────────────────

def _compute_levers(receivables: list, payables: list,
                    od_facility: float, od_utilized: float,
                    treasury_holdings: list) -> dict:
    """
    Compute the 4 cash levers shown on the Overview page.
    Receivables are already normalised (have daysOD).
    Payables are already normalised (have amount, daysLeft, flexibility).
    """
    today = datetime.now().date()

    # Lever 1 — receivables reachable
    certain = probable = risky = 0.0
    for r in receivables:
        bal = r.get("balance", r.get("amount", 0)) or 0
        days_od = r.get("daysOD", 0) or 0
        if r.get("status", "").lower() == "paid":
            continue
        if days_od <= 30:
            certain += bal
        elif days_od <= 60:
            probable += bal
        else:
            risky += bal
    recv_total = certain + probable + risky

    # Lever 2 — OD capacity
    od_available = (od_facility or 0) - (od_utilized or 0)
    od_rate = 12.5  # HDFC OD rate p.a.

    # Lever 3 — treasury by liquidity tier
    tiers: dict[str, float] = {}
    total_treasury = 0.0
    data_stale = False
    for h in treasury_holdings:
        inv_type = (h.get("investmentType") or "other").lower()
        val = float(h.get("currentValue") or 0)
        tiers[inv_type] = tiers.get(inv_type, 0.0) + val
        total_treasury += val
        stmt_date_str = h.get("lastStatementDate")
        if stmt_date_str:
            try:
                from datetime import date as _date
                stmt_date = _date.fromisoformat(str(stmt_date_str))
                if (today - stmt_date).days > 7:
                    data_stale = True
            except Exception:
                pass

    # Lever 4 — vendor stretch
    # Buckets: must-pay | can-delay-7d | can-delay-30d | can-delay-45d | can-delay-60d | can-delay-90d
    must_pay = can_7d = can_30d = can_45d = can_60d = can_90d = 0.0
    for p in payables:
        if p.get("status", "").lower() == "paid":
            continue
        amt = p.get("amount", 0) or 0
        flex = p.get("flexibility", "can-delay-7d")
        if flex == "must-pay":
            must_pay += amt
        elif flex == "can-delay-7d":
            can_7d += amt
        elif flex == "can-delay-30d":
            can_30d += amt
        elif flex == "can-delay-45d":
            can_45d += amt
        elif flex == "can-delay-60d":
            can_60d += amt
        elif flex == "can-delay-90d":
            can_90d += amt
        else:
            can_7d += amt  # unknown → conservative default

    # Rollup: total deferrable = everything except must-pay
    can_defer_total = can_7d + can_30d + can_45d + can_60d + can_90d

    return {
        "receivablesReachable": {
            "total": recv_total,
            "virtuallyCertain": certain,
            "probable": probable,
            "dependsOnClient": risky,
            "bestFor": "Fastest path to cash. Free. Chase before anything else.",
        },
        "odCapacity": {
            "available": od_available,
            "interestRate": od_rate,
            "dailyCost10L": round(10_00_000 * od_rate / 100 / 365),
            "bestFor": "Bridge a gap when receivables won't clear in time. Revolving — repay when cash arrives.",
        },
        "treasuryLiquid": {
            "totalMarketValue": total_treasury,
            "liquid": tiers.get("liquid", 0),
            "debt_short": tiers.get("debt_short", 0),
            "debt_long": tiers.get("debt_long", 0),
            "equity": tiers.get("equity", 0),
            "hybrid": tiers.get("hybrid", 0),
            "fd": tiers.get("fd", 0),
            "dataStale": data_stale,
            "bestFor": "Last resort. Breaking compounding costs more than interest saved.",
            "vrWealthManaged": False,
        },
        "vendorStretch": {
            "mustPayOnTime": must_pay,
            "canStretch7d": can_7d,
            "canStretch30d": can_30d,
            "canStretch45d": can_45d,
            "canStretch60d": can_60d,
            "canStretch90d": can_90d,
            "canDeferTotal": can_defer_total,
            "bestFor": "Buy time without cash. Use sparingly — goodwill erosion compounds.",
        },
    }


# ── 12-Month Cash Flow Projection ──────────────────────────────────────────

# FY 2026-27 calendar: Apr 2026 → Mar 2027
_FY_MONTHS = [
    "2026-04", "2026-05", "2026-06",   # Q1
    "2026-07", "2026-08", "2026-09",   # Q2
    "2026-10", "2026-11", "2026-12",   # Q3
    "2027-01", "2027-02", "2027-03",   # Q4
]

_MONTH_LABELS = [
    "April 2026", "May 2026", "June 2026",
    "July 2026", "August 2026", "September 2026",
    "October 2026", "November 2026", "December 2026",
    "January 2027", "February 2027", "March 2027",
]

_QUARTER_META = [
    ("Q1", "Apr – Jun 2026",
     "Revenue from won deals and receivable settlements. Payroll + vendor pressure; "
     "Carl Bechem collection expected."),
    ("Q2", "Jul – Sep 2026",
     "Mid-year ramp. July pipeline bulge from Bigin confirmed deals. "
     "Saltwater diversification targeted — share drops below 55%."),
    ("Q3", "Oct – Dec 2026",
     "Peak exhibition season. Revenue 35%+ above Q1. "
     "Saltwater at 45% target. New fabricator preferred."),
    ("Q4", "Jan – Mar 2027",
     "Post-peak cooldown. Secure Meters renewal critical Q4. "
     "If not closed, Q1 FY27-28 will face same cash strain."),
]

# Vendor cost as share of monthly revenue when Bigin data is available.
# Exhibition build: 38% margin floor → ~55-62% CP. We use 55% (slightly optimistic).
_VENDOR_PCT = 0.55

# Vendor floor dropped — when there's no close-month activity and no tracked
# projects, vendor outflow is ₹0 (was ₹5L standing). If a real standing cost
# exists, capture it as a recurring entry in Payables instead of a hidden floor.
_VENDOR_FLOOR = 0   # ₹0/month — was ₹5L (dropped per Niloy 20-May-2026)


def _compute_cashflow(
    monthly_revenue: dict,
    monthly_vendor_outflow: dict,
    payroll_monthly: float,
    op_cash: float,
    receivables: list,
    monthly_burn_overrides: Optional[dict] = None,
    monthly_close_revenue: Optional[dict] = None,
    monthly_statutory: Optional[dict] = None,
) -> tuple[dict, list, list, dict]:
    """
    Compute 12-month cash flow projection for FY 2026-27.
    Returns (annual, cashflow_months, quarters, extrapolation)
    """
    # Receivables: map expectedDate (or dueDate) → expected collection this month
    recv_expected: dict[str, float] = {}
    for r in receivables:
        if r.get("status", "").lower() == "paid":
            continue
        expected = r.get("expectedDate") or r.get("dueDate")
        if expected:
            mk = str(expected)[:7]
            recv_expected[mk] = recv_expected.get(mk, 0) + float(r.get("balance", 0) or 0)

    burn_overrides = monthly_burn_overrides or {}
    default_payroll = payroll_monthly or 2_550_000

    cashflow_months = []
    running_cash = op_cash

    for i, mk in enumerate(_FY_MONTHS):
        qn = (i // 3) + 1
        yr, mo = int(mk[:4]), int(mk[5:])
        next_mo = mo + 1 if mo < 12 else 1
        next_yr = yr if mo < 12 else yr + 1
        _MN = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        period = f"{_MN[mo]} {str(yr)[2:]} – {_MN[next_mo]} {str(next_yr)[2:]}"

        in_pipeline = float(monthly_revenue.get(mk, 0) or 0)
        in_recv = float(recv_expected.get(mk, 0) or 0)

        # Vendor outflow priority:
        #   1. Actual project CP from Sonal's Projects sheet (most accurate)
        #   2. 55% of GROSS close-month revenue (work happens at close month,
        #      so CP hits then — not in the month when the trailing 25% cash
        #      lands). This prevents double-counting vendor costs.
        #   3. ₹5L standing floor for zero-revenue months with no tracked projects
        close_rev = float((monthly_close_revenue or {}).get(mk, 0) or 0)
        if mk in monthly_vendor_outflow and monthly_vendor_outflow[mk]:
            out_vendors = float(monthly_vendor_outflow[mk])
        elif close_rev > 0:
            out_vendors = close_rev * _VENDOR_PCT
        else:
            out_vendors = _VENDOR_FLOOR

        # Payroll: per-month CONFIG_MONTHLY_BURN_YYYY-MM override → global fallback
        out_payroll = burn_overrides.get(mk) or default_payroll
        # Statutory: pull from Statutory sheet tab (was flat ₹2.5L/month).
        # Months with no scheduled obligations get ₹0.
        out_statutory = float((monthly_statutory or {}).get(mk, 0) or 0)

        total_in = in_pipeline + in_recv
        total_out = out_vendors + out_payroll + out_statutory
        net = total_in - total_out
        running_cash += net

        # Confidence: near-term confirmed data → HIGH; mid → MEDIUM; far-out → LOW
        if mk <= "2026-06":
            confidence = "HIGH"
        elif mk <= "2026-09":
            confidence = "MEDIUM"
        else:
            confidence = "LOW"

        cashflow_months.append({
            "label": f"Month {i + 1}",
            "period": period,
            "q": qn,
            "inRecv": in_recv,
            "inPipeline": in_pipeline,
            "outVendors": out_vendors,
            "outPayroll": out_payroll,
            "outStatutory": out_statutory,
            "net": net,
            "confidence": confidence,
            "closingCash": running_cash,
        })

    # Quarterly summaries
    quarters = []
    for qn in range(1, 5):
        q_months = [m for m in cashflow_months if m["q"] == qn]
        conf_order = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
        q_conf = min((m["confidence"] for m in q_months),
                     key=lambda c: conf_order.get(c, 0))
        label, period_str, notes = _QUARTER_META[qn - 1]
        quarters.append({
            "label": label,
            "period": period_str,
            "net": sum(m["net"] for m in q_months),
            "inRecv": sum(m["inRecv"] for m in q_months),
            "inPipeline": sum(m["inPipeline"] for m in q_months),
            "outVendors": sum(m["outVendors"] for m in q_months),
            "outPayroll": sum(m["outPayroll"] for m in q_months),
            "outStatutory": sum(m["outStatutory"] for m in q_months),
            "confidence": q_conf,
            "notes": notes,
        })

    # Annual summary
    total_in = sum(m["inRecv"] + m["inPipeline"] for m in cashflow_months)
    total_out = sum(m["outVendors"] + m["outPayroll"] + m["outStatutory"]
                   for m in cashflow_months)
    net_annual = total_in - total_out

    annual = {
        "totalIn": total_in,
        "totalOut": total_out,
        "netAnnual": net_annual,
        "closingProjection": op_cash + net_annual,
    }

    extrapolation = {
        "basis": (
            "Bigin Won + Existing Confirmed deals split 75% advance (close month) + "
            "25% balance (close month + 1, net-30) + "
            "receivable expected collection dates (GSheet). "
            "Vendor cost: actual project CP from Sonal's Projects sheet → "
            "55% of close-month revenue for months without tracked projects → "
            "₹0 for months with no work activity. "
            "Payroll = CONFIG_MONTHLY_BURN (Notes tab). "
            "Statutory = scheduled obligations from Statutory tab (no flat default)."
        ),
        "confidence": "Months 1–3: HIGH (Bigin confirmed) · Months 4–6: MEDIUM (pipeline weighted) · Months 7–12: LOW (estimated)",
        "assumptions": (
            "Payroll stable at current headcount. No large capex. "
            "Saltwater delivery per Bigin close dates. Secure Meters renewal Q4. No black swan."
        ),
    }

    return annual, cashflow_months, quarters, extrapolation


# Stages treated as confirmed revenue for monthly projection.
# "Closed Won 26-27" = delivered/invoiced; "Existing Confirmed" = contracted but upcoming.
# Both belong in the forward revenue picture.
REVENUE_STAGES = {"closed won 26-27", "existing confirmed"}

# Cash flow covers FY 2026-27 only: April 2026 – March 2027.
_FY27_START = "2026-04"
_FY27_END   = "2027-03"


_MONTH_ABBR = {
    "jan": "01", "feb": "02", "mar": "03", "apr": "04", "may": "05", "jun": "06",
    "jul": "07", "aug": "08", "sep": "09", "oct": "10", "nov": "11", "dec": "12",
}

def _parse_delivery_month(raw: str) -> Optional[str]:
    """
    Convert a delivery_month string to 'YYYY-MM'.
    Handles: 'YYYY-MM', 'YYYY-MM-DD', 'YYYY-MM-DD HH:MM:SS',
             'Apr 2026', 'April 2026', 'Apr-26', 'Apr-2026'.
    Returns None if unparseable.
    """
    s = raw.strip()
    if not s:
        return None
    # ISO date/datetime: 'YYYY-MM-DD' or 'YYYY-MM-DD HH:MM:SS'
    # First 7 chars are always 'YYYY-MM' when the string starts with a 4-digit year
    if len(s) >= 7 and s[4] == "-" and s[:4].isdigit():
        candidate = s[:7]
        if len(candidate) == 7 and candidate[4] == "-":
            return candidate
    # Try "Mon YYYY" or "Month YYYY"
    parts = s.replace("-", " ").split()
    if len(parts) == 2:
        mon_raw, yr_raw = parts[0].lower()[:3], parts[1]
        mon = _MONTH_ABBR.get(mon_raw)
        if mon:
            yr = yr_raw if len(yr_raw) == 4 else f"20{yr_raw}"
            return f"{yr}-{mon}"
    return None


def _monthly_statutory_from_obligations(obligations: list) -> dict:
    """
    Sum amountPayable by due month from the Statutory sheet tab.
    Returns {YYYY-MM: total_amount} covering only FY 2026-27.
    Replaces the flat ₹2.5L/month assumption — pulls actual data from
    sheet_statutory.json. Months with no entries get ₹0 (the caller may
    leave them blank rather than assume a default).
    """
    monthly: dict[str, float] = {}
    for o in obligations:
        due = o.get("dueDate")
        if not due:
            continue
        mk = _parse_delivery_month(str(due).strip())
        if not mk or mk < _FY27_START or mk > _FY27_END:
            continue
        amount = float(o.get("amountPayable", 0) or 0)
        if amount <= 0:
            continue
        monthly[mk] = monthly.get(mk, 0.0) + amount
    return monthly


def _monthly_vendor_from_projects(projects: list) -> dict:
    """
    Sum variable_cost_cp by delivery month from the Projects sheet tab.
    Returns {YYYY-MM: total_cp} covering only FY 2026-27.
    This replaces the manual Monthly_Vendor_Outflow_YYYY-MM Notes entries.
    """
    monthly: dict[str, float] = {}
    for p in projects:
        mk = _parse_delivery_month(str(p.get("delivery_month") or "").strip())
        if not mk or mk < _FY27_START or mk > _FY27_END:
            continue
        cp = float(p.get("variable_cost_cp", p.get("variableCost", 0)) or 0)
        monthly[mk] = monthly.get(mk, 0.0) + cp
    return monthly


def _shift_month(mk: str, delta_months: int) -> str:
    """Shift a YYYY-MM key by delta months (positive = forward, negative = back)."""
    yr, mo = int(mk[:4]), int(mk[5:7])
    total = (yr * 12 + (mo - 1)) + delta_months
    new_yr, new_mo = divmod(total, 12)
    return f"{new_yr:04d}-{new_mo + 1:02d}"


# Payment-terms split applied to all Bigin deals:
#   - 75% advance lands in the close month (typical order-placement payment)
#   - 25% balance lands the month after close (net-30 trailing)
_REVENUE_SPLIT_ADVANCE = 0.75
_REVENUE_SPLIT_BALANCE = 0.25


def _monthly_revenue_from_bigin(deals):
    """
    Group Won + Existing Confirmed deals from Bigin into projected CASH
    inflow months using First Rain's standard 75/25 payment-terms model:
       - 75% advance → close_month
       - 25% balance → close_month + 1 (within 30 days post-close)

    Key = "YYYY-MM", value = projected cash inflow for that month.

    Only inflows that fall within FY 2026-27 (Apr 2026 – Mar 2027) are
    retained. This means the 25% balance from a Mar'27 close lands in
    Apr'27 (FY28) and is dropped; Dec'26 close splits 75/Dec + 25/Jan'27
    so Q4 (Jan–Mar 2027) inflows pull from the prior-quarter Bigin deals.

    Deals with no close date go to the undated list only.

    Stages included:
      - "Closed Won 26-27" — delivered / invoiced
      - "Existing Confirmed" — contracted, execution upcoming

    Notes-tab Monthly_Revenue_YYYY-MM entries override individual months.
    """
    monthly: dict[str, float] = {}        # cash inflow by month (75/25 split)
    monthly_close: dict[str, float] = {}  # gross revenue at close month (for vendor calc)
    undated: list[dict] = []

    for d in deals:
        stage = (d.get("stage") or "").strip().lower()
        if stage not in REVENUE_STAGES:
            continue
        close = d.get("close")
        amount = float(d.get("amount") or 0)
        stage_label = d.get("stage", "")
        if not close:
            undated.append({
                "deal": d.get("deal", ""),
                "amount": amount,
                "stage": stage_label,
                "exec": d.get("exec"),
            })
            continue
        close_month = str(close)[:7]  # "YYYY-MM-DD" → "YYYY-MM"
        balance_month = _shift_month(close_month, 1)

        # Track gross revenue at close month — used to compute vendor cost
        # (work happens at close month, so CP hits that month regardless of
        # when the customer pays).
        if _FY27_START <= close_month <= _FY27_END:
            monthly_close[close_month] = (
                monthly_close.get(close_month, 0.0) + amount
            )

        # 75% advance cash — at close month
        if _FY27_START <= close_month <= _FY27_END:
            monthly[close_month] = (
                monthly.get(close_month, 0.0) + amount * _REVENUE_SPLIT_ADVANCE
            )
        # 25% balance cash — month after close
        if _FY27_START <= balance_month <= _FY27_END:
            monthly[balance_month] = (
                monthly.get(balance_month, 0.0) + amount * _REVENUE_SPLIT_BALANCE
            )

    return monthly, undated, monthly_close


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
        first_day = _date(int(mk[:4]), int(mk[5:7]), 1)
        weeks_out = max(0.0, (first_day - today).days / 7.0)
        b = by_month.get(mk, {"value": 0.0, "committed": 0.0,
                              "active": 0.0, "count": 0, "unpriced": 0})
        if mk < cur_mk:
            # Elapsed FY months: shown for the full-year picture (dashboard
            # renders them muted) but never flagged — a thin month that has
            # already passed is history, not an action item.
            severity = "PAST"
        else:
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


def _build_telegram_briefing(
    op_cash, monthly_burn, treasury, od_facility, od_utilized,
    norm_receivables, norm_statutory, treasury_sweep, cf_annual,
    secure_concentration, saltwater_concentration, health_score=None,
    norm_projects=None, bank_latest_balance=None, pipeline_coverage=None
) -> str:
    """Generate the plaintext daily briefing shown on the Alerts tab."""
    from datetime import datetime

    def fmt(n):
        """
        Mirror dashboard JS fmtP() exactly:
          ≥ 1Cr  → X.XXCr  (2 decimal places, matches fmtP .toFixed(2))
          ≥ 1L   → X.XL   (1 decimal place, matches fmtP .toFixed(1))
          ≥ 1K   → XK      (0 decimal places)
          else   → ₹X
        Uses half-up rounding (not Python banker's rounding) to match JS toFixed().
        """
        import math as _math
        if n is None or n == 0:
            return "₹0"
        sign = "-" if n < 0 else ""
        a = abs(n)

        def _round_half_up(x, decimals):
            factor = 10 ** decimals
            return _math.floor(x * factor + 0.5) / factor

        if a >= 10_000_000:
            v = _round_half_up(a / 10_000_000, 2)
            return f"{sign}₹{v:.2f}Cr"
        if a >= 100_000:
            v = _round_half_up(a / 100_000, 1)
            return f"{sign}₹{v:.1f}L"
        if a >= 1_000:
            return f"{sign}₹{round(a/1_000):.0f}K"
        return f"{sign}₹{int(a)}"

    now = datetime.now()
    date_str = now.strftime("%d %b %Y")

    # ── Health score (mirror JS logic) ──────────────────────────────────────
    runway = (op_cash / monthly_burn) if monthly_burn > 0 else 0
    overdue30 = sum(r.get("balance", 0) for r in norm_receivables if (r.get("daysOD") or 0) > 30)
    total_recv = sum(r.get("balance", 0) for r in norm_receivables)
    overdue_pct = overdue30 / total_recv if total_recv > 0 else 0
    total_pay = sum(p.get("amount", p.get("balance", 0)) for p in [])  # payables not in scope here
    ap_ar = 0  # simplified — payables not passed in; dim4 = 15 by default
    stat_overdue = sum(1 for s in norm_statutory if (s.get("daysLeft", 0) or 0) < 5)
    dim1 = 25 if runway >= 6 else 22 if runway >= 3 else 15 if runway >= 2 else 8 if runway >= 1 else 0
    dim2 = 20 if overdue_pct < 0.10 else 15 if overdue_pct < 0.20 else 10 if overdue_pct < 0.35 else 5
    dim3 = 20 if saltwater_concentration < 0.30 else 12 if saltwater_concentration < 0.50 else 5 if saltwater_concentration < 0.70 else 2
    dim4 = 15  # AP/AR ratio — payables not threaded in; assume healthy
    dim5 = 10 if stat_overdue == 0 else 6 if stat_overdue == 1 else 3 if stat_overdue == 2 else 0
    dim6 = 10 if secure_concentration < 0.25 else 6 if secure_concentration < 0.40 else 3 if secure_concentration < 0.55 else 1
    score = dim1 + dim2 + dim3 + dim4 + dim5 + dim6
    grade = "A" if score >= 80 else "B" if score >= 65 else "C" if score >= 50 else "D" if score >= 35 else "F"

    # ── Runway emoji ─────────────────────────────────────────────────────────
    rwy_emoji = "🟢" if runway >= 3 else "🟡" if runway >= 2 else "🔴"

    # ── Header ───────────────────────────────────────────────────────────────
    od_free = od_facility - od_utilized
    od_pct  = round(od_utilized / od_facility * 100) if od_facility else 0
    lines = [
        f"🟢 FIRST RAIN · {date_str} · 08:00 IST",
        "",
        f"💰 Operating: {fmt(op_cash)} · Runway {runway:.1f}mo {rwy_emoji}",
        f"🏦 Treasury {fmt(treasury)} · OD: {fmt(od_utilized)} used · {fmt(od_free)} free / {fmt(od_facility)} ({od_pct}% drawn)",
    ]

    # ── HDFC iMessage vs sheet variation line ────────────────────────────────
    # bank_latest_balance is the latest BALANCE_SNAPSHOT transaction dict (amount
    # field holds the rupee figure), not a bare number. Accept either shape.
    bank_bal = bank_latest_balance
    if isinstance(bank_bal, dict):
        bank_bal = bank_bal.get("amount")
    if isinstance(bank_bal, (int, float)) and bank_bal:
        gap = abs(op_cash - bank_bal)
        if gap > 100_000:  # >₹1L gap
            lines.append(
                f"⚠️ HDFC alert shows {fmt(bank_bal)} — gap {fmt(gap)} vs sheet. Confirm with Sonal."
            )

    # ── Treasury sweep ───────────────────────────────────────────────────────
    lines.append("")
    direction = (treasury_sweep or {}).get("direction", "AT_TARGET")
    verdict = (treasury_sweep or {}).get("verdict", "")
    rationale = (treasury_sweep or {}).get("rationale", "")
    sweep_icon = "⬆" if direction == "OUTWARD" else "⬇" if direction == "INWARD" else "♻" if direction == "REPAY_OD" else "⏸"
    lines.append(f"{sweep_icon} TREASURY SWEEP")
    if verdict:
        lines.append(verdict)
    if rationale:
        lines.append(f"→ {rationale}")

    # ── Collect top 3 ────────────────────────────────────────────────────────
    sorted_recv = sorted(norm_receivables, key=lambda r: -(r.get("daysOD") or 0))
    top_recv = sorted_recv[:3]
    if top_recv:
        lines.append("")
        lines.append("📊 COLLECT (top 3)")
        for r in top_recv:
            client = r.get("client", r.get("company", "—"))
            bal = r.get("balance", 0)
            days_od = r.get("daysOD") or 0
            status = r.get("collectionStatus", "")
            action = "escalate" if status == "ESCALATE" else "chase today" if days_od > 0 else "follow up"
            od_str = f" · {days_od}d OD" if days_od > 0 else ""
            lines.append(f"• {client} · {fmt(bal)}{od_str} · {action}")

    # ── Deficit strategy ─────────────────────────────────────────────────────
    net_annual = (cf_annual or {}).get("netAnnual", 0) or 0
    collectible = sum(r.get("balance", 0) for r in norm_receivables)
    if net_annual < 0:
        lines.append("")
        lines.append("💡 DEFICIT STRATEGY (next 30d)")
        # 60-day net = roughly 2/12 of annual net
        forecast_60d = net_annual / 6
        lines.append(f"Forecast shortfall: {fmt(forecast_60d)}")
        lines.append(f"→ Primary: chase {fmt(collectible)} collectible")
        od_monthly_cost = od_free * 0.00367  # ~4.4% p.a. / 12
        lines.append(f"→ Tactical: OD {fmt(min(od_free, 5_000_000))} if needed (cost {fmt(od_monthly_cost)}/mo)")
        lines.append("→ Do NOT draw treasury")

    # ── Statutory upcoming ───────────────────────────────────────────────────
    upcoming_stat = [s for s in norm_statutory if (s.get("daysLeft") or -999) >= 0 and (s.get("daysLeft") or 999) <= 30]
    upcoming_stat.sort(key=lambda s: s.get("daysLeft", 999))
    if upcoming_stat:
        lines.append("")
        first = upcoming_stat[0]
        days_left = first.get("daysLeft", 0)
        lines.append(f"🏛 STATUTORY ({days_left}d)")
        for s in upcoming_stat[:2]:
            name = s.get("name", s.get("obligationType", "—"))
            amt = s.get("amount", s.get("amountPayable", 0))
            due_raw = s.get("due", s.get("dueDate", ""))
            # Format YYYY-MM-DD → DD-Mon
            try:
                from datetime import datetime as _dt
                due_fmt = _dt.strptime(due_raw[:10], "%Y-%m-%d").strftime("%-d-%b")
            except Exception:
                due_fmt = due_raw
            action = "overdue" if (s.get("daysLeft") or 0) < 0 else "pay on time"
            est = " (est)" if s.get("isEstimate") else ""
            lines.append(f"• {name} · {fmt(amt)}{est} · due {due_fmt} · {action}")

    # ── Projects YTD ─────────────────────────────────────────────────────────
    all_proj = norm_projects or []
    if all_proj:
        total_sp  = sum(p.get("sales_sp", p.get("sales", 0)) or 0 for p in all_proj)
        total_sqm = sum(p.get("sizeSqm", 0) or 0 for p in all_proj)
        lines.append("")
        lines.append(f"📐 PROJECTS YTD ({len(all_proj)} · {int(total_sqm)} sqm · {fmt(total_sp)} SP)")
        for p in all_proj:
            sqm   = p.get("sizeSqm", 0) or 0
            sp    = p.get("sales_sp", p.get("sales", 0)) or 0
            cp    = p.get("variable_cost_cp", p.get("variableCost", 0)) or 0
            cm    = p.get("contributionPct", 0) or 0
            sp_sq = fmt(sp / sqm) if sqm > 0 else "—"
            cp_sq = fmt(cp / sqm) if sqm > 0 else "—"
            client = (p.get("company") or "—")[:22]
            lines.append(f"• {client} · {int(sqm)}sqm · SP/sqm {sp_sq} · CP/sqm {cp_sq} · {cm:.1f}%")

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

    # ── Health ───────────────────────────────────────────────────────────────
    lines.append("")
    lines.append(f"🏥 Health {score}/100 · {grade}")

    return "\n".join(lines)


def _build_sources(bigin, sheet, finance, bank_txn, imessage_data=None) -> list:
    """Build the 5 source status cards shown on the Data tab.
    Each card includes: name, detail, ok (bool), status ('ok'|'stale'|'failed'),
    lastAccessed (ISO str or ''), lastAccessedFmt (human-readable).
    """
    from datetime import timezone

    from datetime import timedelta as _tdelta
    _IST = timezone(_tdelta(hours=5, minutes=30))

    def _parse_iso(s):
        """Return a timezone-aware datetime from an ISO string, or None.
        Naive timestamps (no offset) are assumed to be IST — all local scripts
        use datetime.now() without tzinfo, which is local clock (IST on this Mac)."""
        if not s:
            return None
        try:
            s_clean = s.replace("Z", "+00:00")
            dt = datetime.fromisoformat(s_clean)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=_IST)
            return dt
        except Exception:
            return None

    def _fmt_ts(iso_str):
        """Return (formatted_str, hours_ago) from an ISO timestamp string."""
        dt = _parse_iso(iso_str)
        if dt is None:
            return "—", None
        now = datetime.now(tz=_IST)
        hours_ago = (now - dt).total_seconds() / 3600
        # Format as "25 May · 15:47 IST"
        dt_ist = dt.astimezone(_IST)
        fmt = dt_ist.strftime("%-d %b · %H:%M IST")
        if hours_ago < 0.017:  # < 1 minute
            age = "just now"
        elif hours_ago < 1:
            age = f"{int(hours_ago * 60)}min ago"
        elif hours_ago < 24:
            age = f"{hours_ago:.1f}h ago"
        else:
            age = f"{int(hours_ago / 24)}d ago"
        return f"{fmt} ({age})", hours_ago

    def _status(ok_bool, hours_ago, stale_threshold=10, failed_threshold=30):
        """Return 'ok', 'stale', or 'failed' from hours_ago."""
        if not ok_bool:
            return "failed"
        if hours_ago is None:
            return "ok"  # no timestamp = assume fresh (just written)
        if hours_ago < stale_threshold:
            return "ok"
        if hours_ago < failed_threshold:
            return "stale"
        return "failed"

    sources = []

    # ── Gmail / HDFC bank transactions ───────────────────────────────────────
    txn_meta = bank_txn.get("meta", {}) if bank_txn else {}
    totals = bank_txn.get("totals", {}) if bank_txn else {}
    txn_count = totals.get("transactionCount", 0) or 0
    txns = bank_txn.get("transactions", []) if bank_txn else []
    credit_count = sum(1 for t in txns if (t.get("type") or "").upper() in ("CREDIT", "INWARD"))
    debit_count = txn_count - credit_count
    gmail_ok = txn_count > 0
    gmail_ts_raw = txn_meta.get("read_at", "")
    gmail_ts_fmt, gmail_hrs = _fmt_ts(gmail_ts_raw)
    gmail_detail = (
        f"HDFC alerts parsed: {credit_count} credits, {debit_count} debits in last 7 days"
        if gmail_ok else "No HDFC transactions parsed yet"
    )
    sources.append({
        "name": "Gmail (niloy@firstrain.co.in)",
        "detail": gmail_detail,
        "ok": gmail_ok,
        "status": _status(gmail_ok, gmail_hrs),
        "lastAccessed": gmail_ts_raw,
        "lastAccessedFmt": gmail_ts_fmt,
    })

    # ── Google Sheet ─────────────────────────────────────────────────────────
    recv_count = len(finance.get("receivables", []))
    pay_count = len(finance.get("payables", []))
    proj_count = len(sheet.get("projects", []))
    sheet_tabs = 7  # Cash_Position, Treasury, Receivables, Payables, Statutory, Notes, Projects
    sheet_ok = recv_count > 0 or pay_count > 0 or proj_count > 0
    # Timestamp from sheet_cash_position.json meta.read_at (written by read_cashflow_xlsx.py)
    sheet_ts_raw = ""
    try:
        cp_json = Path("data/projects/sheet_cash_position.json")
        if cp_json.exists():
            cp_data = json.loads(cp_json.read_text())
            sheet_ts_raw = cp_data.get("meta", {}).get("read_at", "")
    except Exception:
        pass
    sheet_ts_fmt, sheet_hrs = _fmt_ts(sheet_ts_raw)
    sheet_detail = f"{sheet_tabs} tabs read, {recv_count} receivables + {pay_count} payables + {proj_count} projects"
    sources.append({
        "name": "Google Sheet (FirstRain-Cashflow-Master)",
        "detail": sheet_detail,
        "ok": sheet_ok,
        "status": _status(sheet_ok, sheet_hrs),
        "lastAccessed": sheet_ts_raw,
        "lastAccessedFmt": sheet_ts_fmt,
    })

    # ── Bigin CRM ────────────────────────────────────────────────────────────
    deals = bigin.get("deals", [])
    active_count = sum(1 for d in deals if d.get("bucket") not in ("junk", "lost", "won"))
    won_count = sum(1 for d in deals if d.get("bucket") == "won")
    junk_count = sum(1 for d in deals if d.get("bucket") == "junk")
    bigin_ok = len(deals) > 0
    bigin_ts_raw = bigin.get("meta", {}).get("fetched_at", "")
    bigin_ts_fmt, bigin_hrs = _fmt_ts(bigin_ts_raw)
    bigin_detail = (
        f"{active_count} active deals in Sales Pipeline 26-27 · {won_count} won · {junk_count} unqualified"
        if bigin_ok else "No pipeline data"
    )
    sources.append({
        "name": "Bigin CRM",
        "detail": bigin_detail,
        "ok": bigin_ok,
        "status": _status(bigin_ok, bigin_hrs),
        "lastAccessed": bigin_ts_raw,
        "lastAccessedFmt": bigin_ts_fmt,
    })

    # ── HDFC SMS / iMessage ───────────────────────────────────────────────────
    sms_meta = (imessage_data or {}).get("meta", {})
    sms_feed = sms_meta.get("feed_status", "unknown")
    sms_bank_feed = sms_meta.get("bank_feed_status", sms_feed)
    sms_stale_but_live = sms_meta.get("bank_stale_but_phone_live", False)
    feed_health = sms_meta.get("feed_health", {})
    last_hdfc_sms = feed_health.get("last_hdfc_sms_date", "")
    hours_since_hdfc = feed_health.get("hours_since_hdfc")
    sms_txn_count = sms_meta.get("transaction_count", 0) or 0
    sms_ts_raw = sms_meta.get("fetched_at", "")
    sms_ts_fmt, _ = _fmt_ts(sms_ts_raw)
    # Status logic — use hours directly so thresholds are enforced here too.
    # Priority: overall relay down (h_any ≥ 24) > bank channel stale (h_hdfc ≥ 20) > ok.
    h_any = feed_health.get("hours_since_any")
    h_hdfc_val = hours_since_hdfc  # already extracted above (may be None)
    if h_any is not None and h_any >= 24:
        # Relay has been down ≥ 24h — entire iMessage feed stalled
        sms_status = "stale" if h_any < 48 else "failed"
        sms_ok = True  # data is just delayed, not missing
    elif sms_stale_but_live or sms_bank_feed == "stale" or (h_hdfc_val is not None and h_hdfc_val >= 20):
        sms_status = "stale"
        sms_ok = True  # phone alive, just bank SMS quiet
    elif sms_bank_feed == "unknown":
        sms_status = "failed"
        sms_ok = sms_txn_count > 0
    else:
        sms_status = "ok"
        sms_ok = True
    # Detail line — surface relay-down warning if overall feed is stale
    od_snaps = (imessage_data or {}).get("od_balance_snapshots", [])
    relay_warn = ""
    if h_any is not None and h_any >= 24:
        relay_warn = f" ⚠️ iMessage relay down {h_any:.0f}h — iPhone→Mac SMS stalled"
    if od_snaps:
        latest_snap = od_snaps[0]
        od_used = latest_snap.get("odUtilized", 0)
        snap_date = (latest_snap.get("date") or "")[:10]
        sms_detail = (
            f"Last HDFC SMS {last_hdfc_sms or snap_date} ({hours_since_hdfc:.0f}h ago)"
            f" · OD ₹{od_used/1e5:.1f}L as of {snap_date}{relay_warn}"
            if hours_since_hdfc is not None else
            f"{sms_txn_count} SMS txns parsed · OD ₹{od_used/1e5:.1f}L{relay_warn}"
        )
    else:
        sms_detail = (
            f"Last HDFC SMS {last_hdfc_sms or '—'} ({hours_since_hdfc:.0f}h ago)"
            f" · {sms_txn_count} txns{relay_warn}"
            if hours_since_hdfc is not None else
            f"Feed {sms_bank_feed} · {sms_txn_count} txns · iMessage chat.db{relay_warn}"
        )
    sources.append({
        "name": "HDFC SMS (iMessage)",
        "detail": sms_detail,
        "ok": sms_ok,
        "status": sms_status,
        "lastAccessed": sms_ts_raw,
        "lastAccessedFmt": sms_ts_fmt,
    })

    # ── Telegram Bot (static — briefing always generated) ────────────────────
    now_fmt = datetime.now().strftime("%-d %b · %H:%M IST")
    sources.append({
        "name": "Telegram Bot (@FirstRainOS1_bot)",
        "detail": "Daily briefing sent at 08:00 IST",
        "ok": True,
        "status": "ok",
        "lastAccessed": datetime.now().astimezone().isoformat(),
        "lastAccessedFmt": f"{now_fmt} (now)",
    })

    return sources


def _compose_cashflow(bigin, sheet, momentum, drift, imessage_data: dict = None):
    """
    Compose the cashflow.json structure the v11 renderer reads.
    imessage_data: pre-loaded hdfc_imessages.json dict (passed in so the SMS OD
    override happens before sweep/levers are computed from the cash dict).
    """
    finance = _load_finance()
    cash = finance.get("cash", {}) or {}

    # ── Normalise receivables and payables (add JS field-name aliases) ──────
    raw_receivables = finance.get("receivables", []) or []
    raw_payables = finance.get("payables", []) or []
    if isinstance(raw_payables, dict):  # legacy: payables was a dict
        raw_payables = []
    raw_statutory = finance.get("statutory", []) or []
    norm_receivables = [_normalize_receivable(r) for r in raw_receivables]
    norm_payables = [_normalize_payable(p) for p in raw_payables]
    norm_statutory = [_normalize_statutory(s) for s in raw_statutory]
    finance["receivables"] = norm_receivables
    finance["payables"] = norm_payables
    finance["statutory"] = norm_statutory

    derived = _compute_derived(bigin, sheet, finance)

    # Monthly revenue: auto from Bigin Won deals, overridden by Notes manual entries
    bigin_monthly_revenue, undated_won, bigin_monthly_close = _monthly_revenue_from_bigin(bigin.get("deals", []))
    notes_overrides = finance.get("notesMonthlyRevenue", {})
    monthly_revenue = {**bigin_monthly_revenue, **notes_overrides}  # Notes wins on conflict

    # Monthly vendor outflow: auto from Projects variable_cost_cp (no manual entry needed)
    monthly_vendor_outflow = _monthly_vendor_from_projects(sheet.get("projects", []))
    # Gross close-month revenue → used for vendor cost estimation (work happens
    # at close month, so CP hits that month regardless of cash timing).
    monthly_close_revenue = bigin_monthly_close
    # Monthly statutory: auto from Statutory sheet tab (was flat ₹2.5L/month)
    monthly_statutory = _monthly_statutory_from_obligations(finance.get("statutory", []))

    # Bank transactions (auto-parsed from HDFC emails by parse_hdfc_emails.py)
    bank_txn = {}
    if BANK_TXN_JSON.exists():
        bank_txn = json.loads(BANK_TXN_JSON.read_text())

    # ── Treasury holdings (for levers tier breakdown) ────────────────────────
    treasury_holdings: list = []
    if TREASURY_JSON.exists():
        th = json.loads(TREASURY_JSON.read_text())
        raw_holdings = th.get("holdings", [])
        # Deduplicate: sheet_treasury.json accumulates one snapshot per
        # statement date — keep only the LATEST snapshot per fund so we
        # don't triple-count when multiple statement dates are present.
        #
        # Dedup key: (folio, investmentType) ONLY — folio uniquely identifies
        # a fund position within an AMC, so name spelling variants must NOT
        # split the same holding into two. (Bug found 06-Jul-2026: Sonal
        # re-entered the Kotak Income Plus Arbitrage Omni FOF folio
        # 15966212/61 with a concatenated name "OmniKotak Income Plus
        # Arbitrage Omni FOF Regular Plan Growth". The old-name row was
        # a ₹30L placeholder and the new-name row was the real ₹42.5L
        # position — three-field dedup kept BOTH, overcounting by ₹30L.)
        seen: dict = {}
        for h in raw_holdings:
            key = (
                h.get("folio", ""),
                h.get("investmentType", h.get("instrument", "")),
            )
            existing_date = seen.get(key, {}).get("lastStatementDate", "")
            if h.get("lastStatementDate", "") >= existing_date:
                seen[key] = h
        treasury_holdings = list(seen.values())

    # ── Override cash position from HDFC SMS when fresher than Sonal's sheet ──
    # The iMessage parser extracts 'Avl bal:INR -X' from 0241 SMS alerts.
    # If that reading is newer than the last sheet date, it becomes the live source.
    # Sheet (Sonal) is still shown for reconciliation; the delta is flagged.
    sms_od = _derive_od_from_sms(imessage_data or {})
    sheet_date = (cash.get("date") or "")[:10]
    od_source = "sheet"
    sms_od_note = None
    if sms_od and sms_od["date"] > sheet_date:
        sheet_od_utilized = cash.get("odUtilized", 0) or 0
        sheet_op_cash = cash.get("operatingCash", 0) or 0
        delta = sms_od["odUtilized"] - sheet_od_utilized
        # Override the cash dict with SMS-authoritative values
        cash["odUtilized"] = sms_od["odUtilized"]
        cash["operatingCash"] = sms_od["operatingCash"]
        cash["odSource"] = "hdfc_sms"
        cash["odDate"] = sms_od["date"]
        od_source = "hdfc_sms"
        sms_od_note = {
            "smsOdDate": sms_od["date"],
            "smsOdUtilized": sms_od["odUtilized"],
            "sheetOdDate": sheet_date,
            "sheetOdUtilized": sheet_od_utilized,
            "delta": delta,
            "deltaFormatted": f"+₹{delta/1e5:.1f}L OD drawn since sheet" if delta > 0 else f"-₹{abs(delta)/1e5:.1f}L OD repaid since sheet",
        }
        print(f"  📱 HDFC SMS OD override: ₹{sms_od['odUtilized']/1e5:.2f}L drawn "
              f"(SMS {sms_od['date']}) vs sheet ₹{sheet_od_utilized/1e5:.2f}L ({sheet_date}). "
              f"Delta: {sms_od_note['deltaFormatted']}")
    elif sms_od:
        cash["odSource"] = "sheet"   # Sheet is fresher — SMS data is older, keep sheet
        print(f"  ℹ HDFC SMS OD ({sms_od['date']}) not newer than sheet ({sheet_date}) — keeping sheet values")
    else:
        cash["odSource"] = "sheet"

    # ── Sweep advisory & levers ───────────────────────────────────────────────
    op_cash = cash.get("operatingCash", 0) or 0
    od_facility = cash.get("odLimit", cash.get("odFacility", 0)) or 0
    od_utilized = cash.get("odUtilized", 0) or 0
    # Treasury total from the DEDUPED holdings. cash.treasury can be inflated
    # (it gets corrupted to ~10x when non-deduped accumulating snapshots are
    # summed upstream), so trust the deduped holdings sum as the real buffer.
    treasury_total = sum(float(h.get("currentValue") or 0) for h in treasury_holdings) or (cash.get("treasury", 0) or 0)
    monthly_burn = finance.get("monthlyBurn") or cash.get("monthlyBurn") or 0
    # Fallback: if no plain CONFIG_MONTHLY_BURN entry, derive from per-month overrides
    if not monthly_burn:
        _notes_burn = finance.get("notesMonthlyBurn") or {}
        if _notes_burn:
            from datetime import date as _date
            _cur_mk = _date.today().strftime("%Y-%m")
            monthly_burn = _notes_burn.get(_cur_mk) or next(iter(_notes_burn.values()), 0)

    sweep_config, treasury_sweep = _compute_sweep(
        op_cash, monthly_burn, od_facility, od_utilized,
        receivables=norm_receivables, payables=norm_payables,
    )
    levers = _compute_levers(
        norm_receivables, norm_payables,
        od_facility, od_utilized, treasury_holdings
    )

    # ── 12-month cash flow projection ─────────────────────────────────────
    cf_annual, cf_months, cf_quarters, cf_extrapolation = _compute_cashflow(
        monthly_revenue, monthly_vendor_outflow, monthly_burn, op_cash, norm_receivables,
        monthly_burn_overrides=finance.get("notesMonthlyBurn", {}),
        monthly_close_revenue=monthly_close_revenue,
        monthly_statutory=monthly_statutory,
    )

    # ── Pipeline coverage by execution month (spec 2026-07-06) ──────────────
    coverage_floor = finance.get("execCoverageFloor") or _COVERAGE_FLOOR_DEFAULT
    pipeline_coverage_meta = _compute_pipeline_coverage_by_month(
        bigin.get("deals", []), datetime.now().date(), floor=coverage_floor
    )

    return {
        "FR": {
            # Project / pipeline data (field-name aliases + region expansion applied)
            "projects": [_normalize_project(p) for p in sheet.get("projects", [])],
            "pipeline": [_normalize_deal(d) for d in bigin.get("deals", [])],
            "momentum": momentum,
            "drift": drift,

            # Cash position — source priority: HDFC SMS (live) > Sheet (Sonal, daily manual)
            # odSource: 'hdfc_sms' when SMS is fresher; 'sheet' otherwise.
            # smsOdReconcile: non-null when SMS overrode the sheet — shows date/delta.
            "operatingCash": op_cash,
            "treasury": treasury_total,
            "odFacility": od_facility,
            "odUtilized": od_utilized,
            "odSource": od_source,
            "smsOdReconcile": sms_od_note,
            "monthlyBurn": monthly_burn,

            # Working capital (normalised field aliases added above)
            "receivables": norm_receivables,
            "payables": norm_payables,
            # Statutory TAB display: only obligations with a real amount (> ₹0).
            # The dozens of ₹0 "projected" filing rows (future GSTR-1, PT-MH, TDS
            # returns with no payment) are dropped from the tab to cut clutter.
            # NOTE: the FULL list (norm_statutory) is still used for the health
            # score, cash-flow projection, and briefing — so ₹0 filing deadlines
            # remain tracked internally; they are only hidden from this tab view.
            "statutory": [s for s in norm_statutory
                          if abs(float(s.get("amount", 0) or 0)) > 0.0],

            # Derived / computed
            "allRegions": derived["allRegions"],
            "allIndustries": derived["allIndustries"],
            "secureConcentration": derived["secureConcentration"],
            "secureRevenue": derived["secureRevenue"],
            "pipelineTotal": derived["pipelineTotal"],
            "saltwaterConcentration": derived["saltwaterConcentration"],
            "saltwaterOutstanding": derived["saltwaterOutstanding"],
            "topActions": derived["topActions"],
            "execNames": EXEC_NAMES,

            # Monthly revenue: auto-computed from Bigin Won deals (by closing month)
            # Notes tab Manual_Revenue_YYYY-MM entries override individual months.
            "monthlyRevenue": monthly_revenue,
            "monthlyRevenueUndated": undated_won,  # Won deals with no close date
            # Monthly outflow: from Notes Monthly_Vendor_Outflow_YYYY-MM entries
            "monthlyVendorOutflow": monthly_vendor_outflow,
            # Bank transactions: auto-parsed from HDFC emails (Steps 5-6)
            "bankTransactions": bank_txn.get("transactions", []),
            "bankTotals": bank_txn.get("totals", {}),
            "bankLatestBalance": bank_txn.get("latestBalance"),
            "bankReconcile": _reconcile_bank_balance(bank_txn),
            "fcyPending": bank_txn.get("fcyPending", []),

            # Treasury sweep advisory + liquidity levers (computed above)
            "sweepConfig": sweep_config,
            "treasurySweep": treasury_sweep,
            "levers": levers,
            # FD holdings — filtered subset of treasury_holdings for dashboard FD card
            "fdHoldings": [h for h in treasury_holdings if (h.get("investmentType") or "").lower() == "fd"],

            # 12-month cash flow projection (computed above)
            "annual": cf_annual,
            "cashflow": cf_months,
            "quarters": cf_quarters,

            # Pipeline coverage by execution month (Bigin Project_Month)
            "pipelineCoverageMeta": pipeline_coverage_meta,

            # Daily briefing (generated from computed data; shown on Alerts tab)
            "telegramBriefing": _build_telegram_briefing(
                op_cash=op_cash,
                monthly_burn=monthly_burn,
                treasury=treasury_total,
                od_facility=od_facility,
                od_utilized=od_utilized,
                norm_receivables=norm_receivables,
                norm_statutory=norm_statutory,
                treasury_sweep=treasury_sweep,
                cf_annual=cf_annual,
                secure_concentration=derived["secureConcentration"],
                saltwater_concentration=derived["saltwaterConcentration"],
                norm_projects=[_normalize_project(p) for p in sheet.get("projects", [])],
                bank_latest_balance=bank_txn.get("latestBalance"),
                pipeline_coverage=pipeline_coverage_meta,
            ),

            "meta": {
                "generated_at": datetime.now().astimezone().isoformat(),
                "bigin_deal_count": bigin["meta"]["count"],
                "sheet_project_count": sheet["meta"]["count"],
                "momentum_mode": momentum["mode"],
                "drift_issues": drift["counts"]["ALERT"],
                "region_source": "bigin" if bigin["meta"]["region_available"] else "regex",
                "industry_source": "bigin" if bigin["meta"]["industry_available"] else "regex",
                "monthly_revenue_source": "bigin_won_deals",
                "monthly_revenue_months": sorted(monthly_revenue.keys()),
                "monthly_revenue_undated_count": len(undated_won),
                "today": datetime.now().strftime("%d %b %Y"),
                "weekEnding": finance.get("weekEnding") or finance.get("_weekEnding"),
            }
        },
        "META": {
            "today": datetime.now().strftime("%d %b %Y"),
            "generated_at": datetime.now().astimezone().isoformat(),
            "extrapolation": cf_extrapolation,
            "lastRefresh": datetime.now().strftime("%d %b %Y · %H:%M IST"),
            "sources": _build_sources(bigin, sheet, finance, bank_txn, imessage_data),
        }
    }


def _render_dashboard(cashflow):
    if not TEMPLATE_PATH.exists():
        raise FileNotFoundError(f"Dashboard template not found at {TEMPLATE_PATH}")

    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    json_str = json.dumps(cashflow, separators=(",", ":"), default=str)

    if "{{CASHFLOW_JSON}}" not in template:
        raise ValueError("Template missing {{CASHFLOW_JSON}} substitution marker")

    rendered = template.replace("{{CASHFLOW_JSON}}", json_str)

    OUTPUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_HTML.write_text(rendered, encoding="utf-8")


def _try_live_bigin_fetch():
    """
    Attempt a live Bigin fetch via the REST client.

    Returns the classified payload if successful, or None if credentials
    are missing (MissingBiginCredentials) — caller falls back to cache.
    Any other error (network, HTTP, parse) is re-raised so failures are
    visible rather than silently served from stale data.
    """
    try:
        from fetch_bigin_pipeline import fetch_pipeline
        from classify_pipeline import classify
        from claude_bigin_client import MissingBiginCredentials
    except ImportError:
        return None   # modules not available (shouldn't happen in normal setup)

    try:
        raw = fetch_pipeline()
        classified = classify(raw)
        print(f"[bigin] Live fetch: {raw['meta']['count']} deals · "
              f"Region={'bigin' if raw['meta']['region_available'] else 'regex'} · "
              f"Industry={'bigin' if raw['meta']['industry_available'] else 'regex'}")
        return classified
    except Exception as exc:
        # Only swallow the "no credentials" case — let everything else bubble up
        if "MissingBiginCredentials" in type(exc).__name__ or "Missing Bigin credentials" in str(exc):
            print(f"[bigin] No API credentials configured → using cached bigin_pipeline_classified.json")
            print(f"        To enable live fetch: copy .env.example → .env and fill in your Bigin tokens.")
            return None
        raise


def build_from_files():
    """
    Rebuild dashboard from JSON files.

    Always attempts a live Bigin fetch first (via claude_bigin_client.py).
    Falls back to the last cached bigin_pipeline_classified.json only if
    BIGIN_* credentials are not configured in .env.
    """
    print("=" * 60)
    print(f"/finance Projects tab build (from-files) · {datetime.now().astimezone().isoformat()}")
    print("=" * 60)

    # ── Live Bigin fetch (always attempted; falls back gracefully) ────────────
    bigin_classified = _try_live_bigin_fetch()
    if bigin_classified is None:
        bigin_classified = json.loads(Path("data/projects/bigin_pipeline_classified.json").read_text())
    sheet = json.loads(Path("data/projects/sheet_projects.json").read_text())
    momentum = json.loads(Path("data/projects/momentum.json").read_text())
    drift = json.loads(Path("data/projects/drift_report.json").read_text())

    # Load iMessage SMS data FIRST so OD override happens inside _compose_cashflow
    imessage_data = _load_imessage_txns()

    cashflow = _compose_cashflow(bigin_classified, sheet, momentum, drift, imessage_data=imessage_data)

    # Attach iMessage data to cashflow output
    cashflow["imessageBankData"] = imessage_data
    _imsg_meta = cashflow["imessageBankData"].get("meta", {})
    cashflow["smsFeedStatus"] = _imsg_meta.get("feed_status", "unknown")
    cashflow["smsFeedHealth"] = _imsg_meta.get("feed_health", {})
    if cashflow["smsFeedStatus"] == "stale":
        fh = cashflow["smsFeedHealth"]
        print(f"  📵 HDFC SMS feed STALE — newest chat.db msg {fh.get('hours_since_any')}h old. "
              f"iPhone->Mac sync likely down; relying on Gmail HDFC email alerts.")
    sms_only = [
        t for t in cashflow["imessageBankData"].get("transactions", [])
        if t.get("confidence") == "sms_only" and t.get("type") == "credit"
    ]
    if sms_only:
        print(f"  ⚠  {len(sms_only)} SMS-only credit(s) not yet in Gmail:")
        for t in sms_only:
            src = " [MANUAL]" if t.get("source") == "manual_paste" else ""
            print(f"     {t['date'][:16]}  ₹{t['amount']:,.0f}  acc:{t['account']}  {t.get('counterparty','?')}{src}")

    CASHFLOW_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(CASHFLOW_JSON, "w") as f:
        json.dump(cashflow, f, indent=2, default=str)

    _render_dashboard(cashflow)

    print("=" * 60)
    print(f"✓ Dashboard rendered → {OUTPUT_HTML}")
    print(f"  drift: {drift['counts']['ALERT']} ALERT · {drift['counts']['WARNING']} WARNING")
    print(f"  momentum: {momentum['mode']} ({momentum['snapshot_count']} snapshots)")
    print(f"  SMS feed: {cashflow['smsFeedStatus']} · {len(cashflow['imessageBankData'].get('transactions', []))} txns")
    print("=" * 60)


if __name__ == "__main__":
    if "--from-files" in sys.argv:
        build_from_files()
    else:
        build()
