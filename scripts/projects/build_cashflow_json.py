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
from classify_pipeline import classify
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

    # Step 6: compose cashflow.json matching v11 renderer schema
    cashflow = _compose_cashflow(bigin_classified, sheet, momentum, drift)

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
        finance["receivables"] = rv.get("receivables", [])

    # --- Payables (new) ---
    if PAYABLES_JSON.exists():
        pv = json.loads(PAYABLES_JSON.read_text())
        finance["payables"] = pv.get("payables", [])

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
        # Monthly revenue overrides (Notes wins over Bigin for that month)
        finance["notesMonthlyRevenue"] = notes.get("monthlyRevenue", {})
        # Per-month burn overrides: CONFIG_MONTHLY_BURN_YYYY-MM rows
        finance["notesMonthlyBurn"] = notes.get("monthlyBurn", {})

    return finance


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
    "RoW": "Rest of the World",
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
    # industry: not in Projects sheet yet → default to Unknown
    if not out.get("industry"):
        out["industry"] = "Unknown"
    # Normalize region short codes
    out["region"] = _REGION_NAME_MAP.get(out.get("region", ""), out.get("region", "Unknown"))
    return out


def _normalize_deal(d: dict) -> dict:
    """Normalize a Bigin pipeline deal: expand region short codes."""
    out = dict(d)
    out["region"] = _REGION_NAME_MAP.get(out.get("region", ""), out.get("region", "Unknown"))
    return out


# ── Treasury Sweep computation ──────────────────────────────────────────────

def _compute_sweep(op_cash: float, monthly_burn: float,
                   od_facility: float, od_utilized: float) -> tuple[dict, dict]:
    """
    Returns (sweepConfig, treasurySweep) dicts for the dashboard Overview card.
    Logic: compare operating cash against 1.5× monthly burn float target.
    """
    float_multiplier = 1.5
    min_sweep = 200_000  # ignore tiny movements

    config = {
        "workingFloatTarget": monthly_burn * float_multiplier,
        "workingFloatMultiplier": float_multiplier,
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

    float_target = monthly_burn * float_multiplier
    od_available = od_facility - od_utilized
    surplus = op_cash - float_target

    def _fmt(n):
        if n >= 10_00_000:
            return f"₹{n/1_00_000:.1f}L"
        if n >= 1_000:
            return f"₹{n/1_000:.0f}K"
        return f"₹{int(n)}"

    if surplus > min_sweep:
        amount = surplus
        sweep = {
            "direction": "OUTWARD",
            "verdict": f"Deploy {_fmt(amount)} to liquid MF",
            "headline": f"{_fmt(amount)} above working float target — invest the surplus",
            "rationale": (
                f"Operating cash {_fmt(op_cash)} exceeds the 1.5× burn target "
                f"({_fmt(float_target)}). Deploy surplus of {_fmt(amount)} to HDFC Liquid Fund "
                f"to earn ~7% p.a. while keeping the float intact."
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
        }
    elif surplus < -min_sweep:
        deficit = abs(surplus)
        if od_available >= deficit:
            verdict = f"Draw OD {_fmt(deficit)} — do not touch treasury"
            rationale = (
                f"Operating cash {_fmt(op_cash)} is {_fmt(deficit)} below the float target "
                f"({_fmt(float_target)}). OD facility has {_fmt(od_available)} available at ~12.5% p.a. "
                f"Draw OD first — cheaper than breaking treasury MF compounding."
            )
            how_to = (
                "HDFC NetBanking → Accounts → Current → Draw OD. "
                "Enter exact amount. Notify Sonal. Repay immediately when receivables clear."
            )
        else:
            verdict = f"Redeem {_fmt(deficit)} from liquid MF (OD insufficient)"
            rationale = (
                f"Operating cash {_fmt(op_cash)} is {_fmt(deficit)} below float target. "
                f"OD headroom ({_fmt(od_available)}) is insufficient. "
                "Redeem liquid MF portion of treasury — do NOT touch debt or equity funds."
            )
            how_to = (
                "HDFC NetBanking → Mutual Funds → Redeem → HDFC Liquid Fund. "
                "Redeem exactly the deficit amount. Confirm with Niloy first."
            )
        sweep = {
            "direction": "INWARD",
            "verdict": verdict,
            "headline": f"{_fmt(deficit)} below float target — cash needs replenishment",
            "rationale": rationale,
            "recommendedAmount": deficit,
            "howTo": how_to,
            "confidence": "HIGH",
            "nextReview": "today before 17:00",
        }
    else:
        sweep = {
            "direction": "AT_TARGET",
            "verdict": "Hold — operating cash at target float",
            "headline": "Operating cash within working float range",
            "rationale": (
                f"Cash {_fmt(op_cash)} is within ±{_fmt(min_sweep)} of the {float_multiplier}× burn "
                f"target ({_fmt(float_target)}). No sweep needed today."
            ),
            "recommendedAmount": 0,
            "confidence": "HIGH",
            "nextReview": "tomorrow 08:00",
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

# Flat vendor standing cost for months with ₹0 revenue (ongoing project work in progress)
_VENDOR_FLOOR = 500_000   # ₹5L/month

# Statutory: flat estimate (GST IGST payable net of input credit + TDS)
_STATUTORY_MONTHLY = 250_000  # ₹2.5L/month


def _compute_cashflow(
    monthly_revenue: dict,
    monthly_vendor_outflow: dict,
    payroll_monthly: float,
    op_cash: float,
    receivables: list,
    monthly_burn_overrides: Optional[dict] = None,
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

        # Vendor outflow: Projects CP (auto) → floor for months with no projects
        if mk in monthly_vendor_outflow and monthly_vendor_outflow[mk]:
            out_vendors = float(monthly_vendor_outflow[mk])
        else:
            out_vendors = _VENDOR_FLOOR

        # Payroll: per-month CONFIG_MONTHLY_BURN_YYYY-MM override → global fallback
        out_payroll = burn_overrides.get(mk) or default_payroll
        out_statutory = _STATUTORY_MONTHLY

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
            "Bigin Won + Existing Confirmed deals by closing month + "
            "receivable expected collection dates (GSheet). "
            "Vendor cost: 55% of monthly revenue (38% margin floor); "
            "floor ₹5L/month for zero-revenue months. "
            "Payroll = CONFIG_MONTHLY_BURN (Notes tab). Statutory = ₹2.5L/month flat."
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
    Handles: 'YYYY-MM', 'Apr 2026', 'April 2026', 'Apr-26', 'Apr-2026'.
    Returns None if unparseable.
    """
    s = raw.strip()
    if not s:
        return None
    # Already YYYY-MM
    if len(s) == 7 and s[4] == "-":
        return s
    # Try "Mon YYYY" or "Month YYYY"
    parts = s.replace("-", " ").split()
    if len(parts) == 2:
        mon_raw, yr_raw = parts[0].lower()[:3], parts[1]
        mon = _MONTH_ABBR.get(mon_raw)
        if mon:
            yr = yr_raw if len(yr_raw) == 4 else f"20{yr_raw}"
            return f"{yr}-{mon}"
    return None


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


def _monthly_revenue_from_bigin(deals):
    """
    Group Won + Existing Confirmed deals from Bigin by closing month.
    Key = "YYYY-MM", value = sum of deal amounts for that month.

    Only deals with close dates within FY 2026-27 (Apr 2026 – Mar 2027) are
    included. Deals closing before Apr 2026 (FY26 history) or after Mar 2027
    are excluded. Deals with no close date go to the undated list only.

    Stages included:
      - "Closed Won 26-27" — delivered / invoiced
      - "Existing Confirmed" — contracted, execution upcoming

    Notes-tab Monthly_Revenue_YYYY-MM entries override individual months.
    """
    monthly: dict[str, float] = {}
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
        month = str(close)[:7]  # "YYYY-MM-DD" → "YYYY-MM"
        if month < _FY27_START or month > _FY27_END:
            continue  # Exclude deals outside FY 2026-27
        monthly[month] = monthly.get(month, 0.0) + amount

    return monthly, undated


def _build_telegram_briefing(
    op_cash, monthly_burn, treasury, od_facility, od_utilized,
    norm_receivables, norm_statutory, treasury_sweep, cf_annual,
    secure_concentration, saltwater_concentration, health_score=None
) -> str:
    """Generate the plaintext daily briefing shown on the Alerts tab."""
    from datetime import datetime

    def fmt(n):
        if n is None or n == 0:
            return "₹0"
        sign = "-" if n < 0 else ""
        a = abs(n)
        if a >= 10_000_000:
            return f"{sign}₹{a/10_000_000:.1f}Cr"
        if a >= 100_000:
            return f"{sign}₹{a/100_000:.1f}L"
        if a >= 1_000:
            return f"{sign}₹{a/1_000:.0f}K"
        return f"{sign}₹{a:.0f}"

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
    lines = [
        f"🟢 FIRST RAIN · {date_str} · 08:00 IST",
        "",
        f"💰 Operating: {fmt(op_cash)} · Runway {runway:.1f}mo {rwy_emoji}",
        f"🏦 Treasury {fmt(treasury)} · OD free {fmt(od_free)}",
    ]

    # ── Treasury sweep ───────────────────────────────────────────────────────
    lines.append("")
    direction = (treasury_sweep or {}).get("direction", "AT_TARGET")
    verdict = (treasury_sweep or {}).get("verdict", "")
    rationale = (treasury_sweep or {}).get("rationale", "")
    sweep_icon = "⬆" if direction == "OUTWARD" else "⬇" if direction == "INWARD" else "⏸"
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
            lines.append(f"• {name} · {fmt(amt)} · due {due_fmt} · {action}")

    # ── Health ───────────────────────────────────────────────────────────────
    lines.append("")
    lines.append(f"🏥 Health {score}/100 · {grade}")

    return "\n".join(lines)


def _build_sources(bigin, sheet, finance, bank_txn) -> list:
    """Build the 4 source status cards shown on the Data tab."""
    sources = []

    # ── Gmail / HDFC bank transactions ───────────────────────────────────────
    txn_meta = bank_txn.get("meta", {}) if bank_txn else {}
    totals = bank_txn.get("totals", {}) if bank_txn else {}
    txn_count = totals.get("transactionCount", 0) or 0
    credits = bank_txn.get("transactions", []) if bank_txn else []
    credit_count = sum(1 for t in credits if (t.get("type") or "").upper() in ("CREDIT", "INWARD"))
    debit_count = txn_count - credit_count
    gmail_ok = txn_count > 0
    gmail_detail = (
        f"HDFC alerts parsed: {credit_count} credits, {debit_count} debits in last 7 days"
        if gmail_ok else "No HDFC transactions parsed yet"
    )
    sources.append({"name": "Gmail (niloy@firstrain.co.in)", "detail": gmail_detail, "ok": gmail_ok})

    # ── Google Sheet ─────────────────────────────────────────────────────────
    recv_count = len(finance.get("receivables", []))
    pay_count = len(finance.get("payables", []))
    proj_count = len(sheet.get("projects", []))
    sheet_tabs = 7  # Cash_Position, Treasury, Receivables, Payables, Statutory, Notes, Projects
    sheet_ok = recv_count > 0 or pay_count > 0 or proj_count > 0
    sheet_detail = f"{sheet_tabs} tabs read, {recv_count} receivables + {pay_count} payables + {proj_count} projects"
    sources.append({"name": "Google Sheet (FirstRain-Cashflow-Master)", "detail": sheet_detail, "ok": sheet_ok})

    # ── Bigin CRM ────────────────────────────────────────────────────────────
    deals = bigin.get("deals", [])
    active_count = sum(1 for d in deals if d.get("bucket") not in ("junk", "lost", "won"))
    won_count = sum(1 for d in deals if d.get("bucket") == "won")
    junk_count = sum(1 for d in deals if d.get("bucket") == "junk")
    bigin_ok = len(deals) > 0
    bigin_detail = (
        f"{active_count} active deals in Sales Pipeline 26-27 · {won_count} won · {junk_count} unqualified"
        if bigin_ok else "No pipeline data"
    )
    sources.append({"name": "Bigin CRM", "detail": bigin_detail, "ok": bigin_ok})

    # ── Telegram Bot (static — briefing always generated) ────────────────────
    sources.append({
        "name": "Telegram Bot (@FirstRainOS1_bot)",
        "detail": "Daily briefing sent at 08:00 IST",
        "ok": True
    })

    return sources


def _compose_cashflow(bigin, sheet, momentum, drift):
    """
    Compose the cashflow.json structure the v11 renderer reads.
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
    bigin_monthly_revenue, undated_won = _monthly_revenue_from_bigin(bigin.get("deals", []))
    notes_overrides = finance.get("notesMonthlyRevenue", {})
    monthly_revenue = {**bigin_monthly_revenue, **notes_overrides}  # Notes wins on conflict

    # Monthly vendor outflow: auto from Projects variable_cost_cp (no manual entry needed)
    monthly_vendor_outflow = _monthly_vendor_from_projects(sheet.get("projects", []))

    # Bank transactions (auto-parsed from HDFC emails by parse_hdfc_emails.py)
    bank_txn = {}
    if BANK_TXN_JSON.exists():
        bank_txn = json.loads(BANK_TXN_JSON.read_text())

    # ── Treasury holdings (for levers tier breakdown) ────────────────────────
    treasury_holdings: list = []
    if TREASURY_JSON.exists():
        th = json.loads(TREASURY_JSON.read_text())
        treasury_holdings = th.get("holdings", [])

    # ── Sweep advisory & levers ───────────────────────────────────────────────
    op_cash = cash.get("operatingCash", 0) or 0
    od_facility = cash.get("odLimit", cash.get("odFacility", 0)) or 0
    od_utilized = cash.get("odUtilized", 0) or 0
    monthly_burn = finance.get("monthlyBurn") or cash.get("monthlyBurn") or 0

    sweep_config, treasury_sweep = _compute_sweep(
        op_cash, monthly_burn, od_facility, od_utilized
    )
    levers = _compute_levers(
        norm_receivables, norm_payables,
        od_facility, od_utilized, treasury_holdings
    )

    # ── 12-month cash flow projection ─────────────────────────────────────
    cf_annual, cf_months, cf_quarters, cf_extrapolation = _compute_cashflow(
        monthly_revenue, monthly_vendor_outflow, monthly_burn, op_cash, norm_receivables,
        monthly_burn_overrides=finance.get("notesMonthlyBurn", {}),
    )

    return {
        "FR": {
            # Project / pipeline data (field-name aliases + region expansion applied)
            "projects": [_normalize_project(p) for p in sheet.get("projects", [])],
            "pipeline": [_normalize_deal(d) for d in bigin.get("deals", [])],
            "momentum": momentum,
            "drift": drift,

            # Cash position (from sheet_cash_position.json; odLimit = OD facility limit)
            "operatingCash": op_cash,
            "treasury": cash.get("treasury", 0),
            # parser writes "odLimit" (the OD facility ceiling); legacy wrote "odFacility"
            "odFacility": od_facility,
            "odUtilized": od_utilized,
            # monthlyBurn from Notes CONFIG_MONTHLY_BURN entry; not a Sheet column
            "monthlyBurn": monthly_burn,

            # Working capital (normalised field aliases added above)
            "receivables": norm_receivables,
            "payables": norm_payables,
            "statutory": norm_statutory,

            # Derived / computed
            "allRegions": derived["allRegions"],
            "allIndustries": derived["allIndustries"],
            "secureConcentration": derived["secureConcentration"],
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
            "fcyPending": bank_txn.get("fcyPending", []),

            # Treasury sweep advisory + liquidity levers (computed above)
            "sweepConfig": sweep_config,
            "treasurySweep": treasury_sweep,
            "levers": levers,

            # 12-month cash flow projection (computed above)
            "annual": cf_annual,
            "cashflow": cf_months,
            "quarters": cf_quarters,

            # Daily briefing (generated from computed data; shown on Alerts tab)
            "telegramBriefing": _build_telegram_briefing(
                op_cash=op_cash,
                monthly_burn=monthly_burn,
                treasury=cash.get("treasury", 0),
                od_facility=od_facility,
                od_utilized=od_utilized,
                norm_receivables=norm_receivables,
                norm_statutory=norm_statutory,
                treasury_sweep=treasury_sweep,
                cf_annual=cf_annual,
                secure_concentration=derived["secureConcentration"],
                saltwater_concentration=derived["saltwaterConcentration"],
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
            "sources": _build_sources(bigin, sheet, finance, bank_txn),
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

    cashflow = _compose_cashflow(bigin_classified, sheet, momentum, drift)

    CASHFLOW_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(CASHFLOW_JSON, "w") as f:
        json.dump(cashflow, f, indent=2, default=str)

    _render_dashboard(cashflow)

    print("=" * 60)
    print(f"✓ Dashboard rendered → {OUTPUT_HTML}")
    print(f"  drift: {drift['counts']['ALERT']} ALERT · {drift['counts']['WARNING']} WARNING")
    print(f"  momentum: {momentum['mode']} ({momentum['snapshot_count']} snapshots)")
    print("=" * 60)


if __name__ == "__main__":
    if "--from-files" in sys.argv:
        build_from_files()
    else:
        build()
