"""
drift_check.py
==============
Reconciles Bigin Closed Won deals against Sheet Projects tab.

Detects:
  1. Bigin Closed Won with no matching Sheet row (after 5 business days)
  2. Sheet row with no matching Bigin deal (soft-match only)

Matching strategy: normalised company name + delivery month within 60 days
of Bigin close date. No Bigin Deal ID required — Sonal doesn't need to
look up URLs.

Output: data/projects/drift_report.json
        (consumed by Telegram briefing script)

Usage:
    python drift_check.py
    # or from orchestrator:
    from drift_check import check
    report = check(classified_pipeline, sheet_projects)
"""

import json
import re
from datetime import datetime, date, timedelta
from pathlib import Path

BIGIN_PATH = Path("data/projects/bigin_pipeline_classified.json")
SHEET_PATH = Path("data/projects/sheet_projects.json")
OUTPUT_PATH = Path("data/projects/drift_report.json")

STALE_WIN_BUSINESS_DAYS = 5        # Bigin Closed Won must appear in Sheet within 5 biz days


# ---------- Helpers ----------

def _normalize_name(name):
    if not name:
        return ""
    s = name.lower().strip()
    # Strip common entity suffixes
    s = re.sub(
        r'\s+(india|systems|pvt|private|limited|ltd|inc|llc|co\.?|corporation|corp|gmbh|bv|sa|ag|srl|spa|plc)\.?(\s|$)',
        ' ', s
    )
    s = re.sub(r'\s+', ' ', s).strip()
    return s


def _parse_date(s):
    if not s:
        return None
    try:
        if "T" in str(s):
            return datetime.fromisoformat(str(s).replace("Z", "+00:00")).date()
        return date.fromisoformat(str(s)[:10])
    except (ValueError, TypeError):
        return None


def _business_days_between(d1, d2):
    """Count business days between two dates (inclusive of endpoints)."""
    if not d1 or not d2:
        return 0
    if d1 > d2:
        d1, d2 = d2, d1
    days = 0
    current = d1
    while current <= d2:
        if current.weekday() < 5:
            days += 1
        current += timedelta(days=1)
    return days


def _month_close(date1, date2):
    """True if two dates are within 60 days of each other."""
    if not date1 or not date2:
        return False
    return abs((date1 - date2).days) <= 60


# ---------- Checks ----------

def _build_sheet_soft_index(sheet_rows):
    index = []
    for r in sheet_rows:
        dm = r.get("delivery_month")
        try:
            dm_date = date.fromisoformat(dm + "-01") if dm and len(dm) == 7 else None
        except ValueError:
            dm_date = None
        index.append({
            "projectNo": r.get("projectNo"),
            "norm_name": _normalize_name(r.get("company")),
            "delivery_date": dm_date,
        })
    return index


def _check_bigin_wins_missing_from_sheet(bigin_wins, sheet_rows, today):
    """Every Bigin Closed Won deal must soft-match a Sheet row within 5 business days."""
    issues = []
    soft_index = _build_sheet_soft_index(sheet_rows)

    for win in bigin_wins:
        deal_id = win.get("id")
        close_date = _parse_date(win.get("close")) or _parse_date(win.get("modified"))
        norm_name = _normalize_name(win.get("account_name"))

        matches = [
            e["projectNo"] for e in soft_index
            if e["norm_name"] == norm_name and _month_close(close_date, e["delivery_date"])
        ]

        if matches:
            continue  # found — all good

        if close_date:
            biz_days = _business_days_between(close_date, today)
            if biz_days >= STALE_WIN_BUSINESS_DAYS:
                issues.append({
                    "severity": "ALERT",
                    "type": "bigin_won_not_in_sheet",
                    "message": f"{win.get('account_name')} (Bigin {deal_id}) closed {biz_days} biz days ago — no Projects row found. Sonal: add project.",
                    "bigin_deal_id": deal_id,
                    "close_date": close_date.isoformat(),
                })
                continue

        issues.append({
            "severity": "INFO",
            "type": "bigin_won_pending_sheet",
            "message": f"{win.get('account_name')} (Bigin {deal_id}) closed recently, awaiting Projects row.",
            "bigin_deal_id": deal_id,
        })

    return issues


def _check_sheet_unmatched(sheet_rows, bigin_wins):
    """Sheet rows with no soft-match in Bigin Won deals — possible orphan or stale row."""
    issues = []
    for row in sheet_rows:
        norm_name = _normalize_name(row.get("company"))
        dm = row.get("delivery_month")
        try:
            dm_date = date.fromisoformat(dm + "-01") if dm and len(dm) == 7 else None
        except ValueError:
            dm_date = None

        matched = any(
            _normalize_name(w.get("account_name")) == norm_name
            and _month_close(_parse_date(w.get("close")), dm_date)
            for w in bigin_wins
        )
        if not matched:
            issues.append({
                "severity": "WARNING",
                "type": "sheet_row_no_bigin_match",
                "message": f"Projects row {row.get('projectNo')} ({row.get('company')}) has no matching Bigin Closed Won deal. Historic project or stale row?",
                "projectNo": row.get("projectNo"),
            })
    return issues


# ---------- Entrypoint ----------

def check(classified_payload, sheet_payload):
    deals = classified_payload["deals"]
    sheet_rows = sheet_payload["projects"]

    bigin_wins = [d for d in deals if d.get("bucket") == "won"]

    today = datetime.now().astimezone().date()

    issues = []
    issues.extend(_check_bigin_wins_missing_from_sheet(bigin_wins, sheet_rows, today))
    issues.extend(_check_sheet_unmatched(sheet_rows, bigin_wins))

    counts = {
        "ALERT": len([i for i in issues if i["severity"] == "ALERT"]),
        "WARNING": len([i for i in issues if i["severity"] == "WARNING"]),
        "INFO": len([i for i in issues if i["severity"] == "INFO"]),
    }

    report = {
        "checked_at": datetime.now().astimezone().isoformat(),
        "bigin_won_count": len(bigin_wins),
        "sheet_row_count": len(sheet_rows),
        "issues": issues,
        "counts": counts,
        "wip_gap": counts["ALERT"],  # renderer uses this directly
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(report, f, indent=2, default=str)

    print(f"[drift_check] ALERT={counts['ALERT']} · WARNING={counts['WARNING']} · INFO={counts['INFO']}")
    return report


if __name__ == "__main__":
    with open(BIGIN_PATH) as f:
        classified = json.load(f)
    with open(SHEET_PATH) as f:
        sheet = json.load(f)
    check(classified, sheet)
