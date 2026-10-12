#!/usr/bin/env python3
"""HDFC BizBlack credit-card model for the CFO OS dashboard + daily syncs.

Input : data/projects/sheet_cards.json (written by read_cashflow_xlsx.py from the
        Credit_Cards / Card_Txns / Card_Config tabs of the Cashflow Master sheet).
Output: the FR.cards block consumed by dashboards/dashboard-template.html, the
        Telegram briefing and the scheduled syncs.

Policies (Niloy, 2026-10-12):
  * Funding order: exhaust card limits FIRST for card-payable items (GST, income
    tax/TDS, SmartPay bills, travel), then OD, treasury last.
  * Clear each card spend by use-date + (floatDaysMax - clearBufferDays) days
    (55 - 7 = 48), never later than HDFC's actual bill due date.
  * Card dues inside priorityWindowDays (or overdue) surface in Priority today.

Only the last 4 digits of a card are ever stored. Never put a full PAN/CVV here.
"""
from __future__ import annotations

import calendar
import json
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

SHEET_CARDS_JSON = Path("data/projects/sheet_cards.json")
LAST_SENT_JSON = Path("data/projects/_cache/cards_last_sent.json")

DEFAULTS = {
    "rewardPct": 1.25,          # effective reward % — confirm from card T&C (flagged in UI until set in sheet)
    "rpValueInr": 1.0,          # 1 RP = Re 1 (HDFC welcome letter, SmartBuy)
    "floatDaysMax": 55,         # "up to 55 days interest-free" (HDFC welcome letter)
    "clearBufferDays": 7,
    "priorityWindowDays": 7,
    "utilisationAlertPct": 70.0,
    "gatewayFeePct": None,      # unverified until Sonal enters it
    "fundingOrder": "cards > OD > treasury",
}
CONFIG_KEYS = {
    "card_reward_pct_effective": "rewardPct",
    "card_gateway_fee_pct": "gatewayFeePct",
    "card_float_days_max": "floatDaysMax",
    "card_clear_buffer_days": "clearBufferDays",
    "card_priority_window_days": "priorityWindowDays",
    "card_utilisation_alert_pct": "utilisationAlertPct",
    "card_funding_order": "fundingOrder",
}
STATUTORY_CATEGORIES = {"gst", "income tax", "tds", "tcs", "advance tax", "statutory", "pf", "pt"}
# Obligations the issuer's 5X category covers when paid on the portals.
CARD_ELIGIBLE_RE = re.compile(r"GST|TDS|TCS|INCOME|ADVANCE", re.I)
STALE_AFTER_DAYS = 2


def _num(v, default=0.0) -> float:
    try:
        if v is None or v == "":
            return default
        return float(str(v).replace(",", ""))
    except (TypeError, ValueError):
        return default


def _iso(v) -> str | None:
    if not v:
        return None
    s = str(v)[:10]
    try:
        date.fromisoformat(s)
        return s
    except ValueError:
        return None


def _d(v) -> date | None:
    s = _iso(v)
    return date.fromisoformat(s) if s else None


def _config(raw_cfg: dict) -> dict:
    A = dict(DEFAULTS)
    A["rewardPctSource"] = "default"
    A["gatewayFeeVerified"] = False
    for k, tgt in CONFIG_KEYS.items():
        if k not in raw_cfg:
            continue
        v = raw_cfg[k]
        if tgt == "fundingOrder":
            if v:
                A[tgt] = str(v)
        elif v in (None, ""):
            continue
        else:
            A[tgt] = _num(v, DEFAULTS[tgt] if DEFAULTS[tgt] is not None else 0.0)
            if tgt == "rewardPct":
                A["rewardPctSource"] = "sheet"
            if tgt == "gatewayFeePct":
                A["gatewayFeeVerified"] = True
    for k in ("floatDaysMax", "clearBufferDays", "priorityWindowDays"):
        A[k] = int(A[k])
    return A


def bill_due(stmt_day: int, due_gap_days: int, use: date) -> date:
    """HDFC bill due date for a spend made on `use` (statement on stmt_day, due stmt + gap)."""
    def stmt_in(y, m):
        return date(y, m, min(int(stmt_day), calendar.monthrange(y, m)[1]))
    st = stmt_in(use.year, use.month)
    if use > st:
        y, m = (use.year + 1, 1) if use.month == 12 else (use.year, use.month + 1)
        st = stmt_in(y, m)
    return st + timedelta(days=int(due_gap_days))


def clear_by(card: dict, use: date, A: dict) -> tuple[date, str]:
    """use + (float - buffer) days, capped at HDFC's actual bill due date."""
    win = A["floatDaysMax"] - A["clearBufferDays"]
    rule = use + timedelta(days=win)
    bd = bill_due(card["stmtDay"], card["dueGapDays"], use)
    return (bd, "HDFC bill due") if bd < rule else (rule, f"use + {win}d")


def _is_demo(row: dict) -> bool:
    return str(row.get("updated_by") or "").strip().upper() == "DEMO" or \
        str(row.get("notes") or "").strip().upper().startswith("DEMO")


def compute_cards(raw: dict | None, today: date | None = None, statutory: list | None = None) -> dict | None:
    """Build FR.cards. Returns None when the tabs are absent/empty (UI then hides cards)."""
    if not raw or not raw.get("present") or not raw.get("cards"):
        return None
    today = today or date.today()
    A = _config(raw.get("config") or {})

    txns = []
    for t in raw.get("txns") or []:
        txns.append({
            "date": _iso(t.get("date")), "card": str(t.get("card_last4") or "").zfill(4),
            "desc": str(t.get("description") or ""), "cat": str(t.get("category") or ""),
            "amt": _num(t.get("amount")), "linked": str(t.get("linked_obligation") or ""),
            "challan": str(t.get("challan_ref") or ""),
            "points": int(_num(t.get("points_earned"))),
            "clearedOn": _iso(t.get("cleared_on")), "demo": _is_demo(t),
        })
    txns = [t for t in txns if t["date"] and t["amt"] > 0]

    cards, demo = [], False
    for r in raw["cards"]:
        last4 = str(r.get("card_last4") or "").zfill(4)
        limit = _num(r.get("credit_limit"))
        outstanding = _num(r.get("outstanding"))
        c = {
            "last4": last4, "holder": str(r.get("card_holder") or ""),
            "product": str(r.get("product") or "HDFC BizBlack"),
            "limit": limit, "outstanding": outstanding,
            "available": _num(r.get("available"), max(0.0, limit - outstanding)) or max(0.0, limit - outstanding),
            "points": int(_num(r.get("reward_points"))),
            "stmtDay": int(_num(r.get("statement_day"), 15)) or 15,
            "dueGapDays": int(_num(r.get("due_gap_days"), 25)) or 25,
            "activated": _iso(r.get("activated_on")),
            "welcomeTarget": _num(r.get("welcome_spend_target")),
            "welcomeDeadline": _iso(r.get("welcome_deadline")),
            "asOf": _iso(r.get("as_of_date")), "demo": _is_demo(r),
        }
        c["available"] = max(0.0, limit - outstanding)
        c["utilPct"] = round(outstanding / limit * 100) if limit else 0
        demo = demo or c["demo"]
        cards.append(c)
    by_last4 = {c["last4"]: c for c in cards}

    open_items = []
    for t in txns:
        c = by_last4.get(t["card"])
        t["stat"] = t["cat"].strip().lower() in STATUTORY_CATEGORIES or bool(t["linked"])
        t["clearBy"], t["clearByDays"], t["basis"] = None, None, None
        if c and not t["clearedOn"]:
            cb, basis = clear_by(c, date.fromisoformat(t["date"]), A)
            t["clearBy"], t["clearByDays"], t["basis"] = cb.isoformat(), (cb - today).days, basis
            open_items.append(t)
        demo = demo or t["demo"]

    for c in cards:
        mine = [t for t in open_items if t["card"] == c["last4"]]
        mine.sort(key=lambda t: t["clearBy"])
        c["earliestClearBy"] = ({"date": mine[0]["clearBy"], "days": mine[0]["clearByDays"], "basis": mine[0]["basis"]}
                                if mine else None)
        nxt = bill_due(c["stmtDay"], c["dueGapDays"], today)
        st = nxt - timedelta(days=c["dueGapDays"])
        c["nextStatement"], c["nextDue"] = st.isoformat(), nxt.isoformat()
        spent = sum(t["amt"] for t in txns if t["card"] == c["last4"])
        c["welcomeSpent"] = spent
        c["welcomePct"] = min(100, round(spent / c["welcomeTarget"] * 100)) if c["welcomeTarget"] else None

    # Due items: open spends whose clear-by falls inside the priority window (or is overdue)
    groups: dict[tuple, dict] = {}
    for t in open_items:
        if t["clearByDays"] > A["priorityWindowDays"]:
            continue
        k = (t["card"], t["clearBy"])
        g = groups.setdefault(k, {"card": t["card"], "holder": by_last4[t["card"]]["holder"], "date": t["clearBy"],
                                  "days": t["clearByDays"], "amt": 0.0, "n": 0, "basis": t["basis"]})
        g["amt"] += t["amt"]
        g["n"] += 1
    due_items = sorted(groups.values(), key=lambda g: g["days"])
    for g in due_items:
        g["severity"] = "red" if g["days"] <= 3 else "amber"

    limit = sum(c["limit"] for c in cards)
    outstanding = sum(c["outstanding"] for c in cards)
    totals = {"limit": limit, "outstanding": outstanding, "available": max(0.0, limit - outstanding),
              "points": sum(c["points"] for c in cards),
              "utilPct": round(outstanding / limit * 100) if limit else 0}

    as_of_dates = [d for d in (_d(c["asOf"]) for c in cards) if d]
    as_of = max(as_of_dates).isoformat() if as_of_dates else None
    age = (today - max(as_of_dates)).days if as_of_dates else None
    warnings = list(raw.get("meta", {}).get("warnings", []))
    if age is None:
        warnings.append("no as_of_date on Credit_Cards")
    elif age > STALE_AFTER_DAYS:
        warnings.append(f"Credit_Cards as_of_date is {age}d old")
    if totals["utilPct"] >= A["utilisationAlertPct"]:
        warnings.append(f"utilisation {totals['utilPct']}% >= {A['utilisationAlertPct']:.0f}% alert")
    if not A["gatewayFeeVerified"]:
        warnings.append("gateway fee on tax-by-card unverified (card_gateway_fee_pct blank)")

    out = {
        "present": True, "isDemo": demo, "asOf": as_of, "asOfAgeDays": age,
        "assumptions": A, "cards": cards, "txns": txns, "totals": totals,
        "dueItems": due_items, "warnings": warnings,
    }
    out["statutoryPlan"] = statutory_plan(out, statutory or [], today)
    return out


def statutory_plan(cards_block: dict, statutory: list, today: date) -> dict:
    """Allocate unpaid, card-eligible statutory items to available card limit (cards first, then OD)."""
    A = cards_block["assumptions"]
    left = {c["last4"]: c["available"] for c in cards_block["cards"]}
    by = {c["last4"]: c for c in cards_block["cards"]}
    rows, card_total, reward_total = [], 0.0, 0.0
    unpaid = [s for s in statutory
              if str(s.get("status", "")).lower() != "filed" and _num(s.get("amount", s.get("amountPayable"))) > 0]
    unpaid.sort(key=lambda s: s.get("daysLeft") if s.get("daysLeft") is not None else s.get("daysToDue", 0) or 0)
    for s in unpaid:
        amt = _num(s.get("amount", s.get("amountPayable")))
        name = str(s.get("name") or s.get("obligationType") or "")
        due = _d(s.get("due") or s.get("dueDate")) or today
        pay_date = max(due, today)
        eligible = bool(CARD_ELIGIBLE_RE.search(name))
        rem, routes = amt, []
        if eligible:
            for last4, avail in left.items():
                take = min(rem, avail)
                if take <= 0:
                    continue
                left[last4] -= take
                rem -= take
                card_total += take
                reward_total += take * A["rewardPct"] / 100
                cb, basis = clear_by(by[last4], pay_date, A)
                routes.append({"card": last4, "holder": by[last4]["holder"], "amt": take,
                               "clearBy": cb.isoformat(), "days": (cb - pay_date).days, "basis": basis})
        rows.append({"name": name, "period": str(s.get("periodFor") or "")[:7], "due": due.isoformat(),
                     "amount": amt, "eligible": eligible, "routes": routes, "odAmt": rem})
    return {"rows": rows, "cardRoutable": card_total, "estReward": reward_total,
            "feeVerified": A["gatewayFeeVerified"], "rewardPct": A["rewardPct"],
            "feeExceedsReward": bool(A["gatewayFeeVerified"] and (A["gatewayFeePct"] or 0) >= A["rewardPct"])}


# ---------- text helpers (Telegram / syncs) ----------

def _fmt(n: float) -> str:
    a = abs(n)
    if a >= 10_000_000:
        return f"₹{n / 10_000_000:.2f}Cr"
    if a >= 100_000:
        return f"₹{n / 100_000:.1f}L"
    if a >= 1000:
        return f"₹{n / 1000:.0f}K"
    return f"₹{n:.0f}"


def _dfmt(iso: str) -> str:
    d = date.fromisoformat(iso)
    return f"{d.day} {d.strftime('%b')}"


def due_line(g: dict) -> str:
    when = f"{abs(g['days'])}d overdue" if g["days"] < 0 else ("due today" if g["days"] == 0 else f"due in {g['days']}d")
    who = f"{g['holder']} ·{g['card']}" if g.get("holder") else f"·{g['card']}"
    return f"Pay HDFC card {who} · {_fmt(g['amt'])} · {when} (clear by {_dfmt(g['date'])})"


def pulse_line(block: dict | None) -> str:
    """One-line finance-pulse fragment for Telegram, e.g. '💳 ₹4.1L/₹8.0L (51%) · next ₹60K 16 Oct'."""
    if not block:
        return ""
    t = block["totals"]
    nxt = ""
    opened = [c["earliestClearBy"] for c in block["cards"] if c.get("earliestClearBy")]
    if opened:
        e = min(opened, key=lambda x: x["date"])
        nxt = f" · next clear-by {_dfmt(e['date'])} ({e['days']}d)"
    demo = " [DEMO]" if block.get("isDemo") else ""
    return f"💳 {_fmt(t['outstanding'])}/{_fmt(t['limit'])} ({t['utilPct']}%){nxt}{demo}"


def health_issues(block: dict | None, present_in_sheet: bool) -> list[str]:
    issues = []
    if not present_in_sheet or not block:
        return ["Credit_Cards tabs missing/empty in the Cashflow Master (cards section hidden)"]
    if block.get("isDemo"):
        issues.append("cards still on DEMO data — Sonal to replace with actuals")
    age = block.get("asOfAgeDays")
    if age is None or age > STALE_AFTER_DAYS:
        issues.append(f"Credit_Cards as_of_date stale ({'unset' if age is None else f'{age}d old'})")
    for g in block.get("dueItems", []):
        if g["days"] <= 3:
            issues.append(due_line(g))
    if block["totals"]["utilPct"] >= block["assumptions"]["utilisationAlertPct"]:
        issues.append(f"card utilisation {block['totals']['utilPct']}% >= alert")
    return issues


# ---------- delta (midday / EOD) ----------

def snapshot(block: dict | None) -> dict:
    if not block:
        return {}
    return {"outstanding": block["totals"]["outstanding"],
            "dueKeys": sorted(f"{g['card']}|{g['date']}|{int(g['amt'])}" for g in block["dueItems"]),
            "txnCount": len(block["txns"]), "asOf": block.get("asOf")}


def delta_lines(block: dict | None, last: dict | None) -> list[str]:
    """What changed since the last sync that sent a card update. Empty list = say nothing."""
    if not block:
        return []
    cur, last = snapshot(block), (last or {})
    lines = []
    if not last:
        return [pulse_line(block)] if block["dueItems"] else []
    d_out = cur["outstanding"] - last.get("outstanding", 0)
    if abs(d_out) >= 1:
        lines.append(f"💳 card outstanding {'+' if d_out > 0 else '−'}{_fmt(abs(d_out))} → {_fmt(cur['outstanding'])} of {_fmt(block['totals']['limit'])}")
    new_due = [g for g in block["dueItems"] if f"{g['card']}|{g['date']}|{int(g['amt'])}" not in set(last.get("dueKeys", []))]
    lines += [f"💳 {due_line(g)}" for g in new_due]
    return lines


def _load(path: Path):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return None


def _cli(argv: list[str]) -> int:
    cmd = argv[1] if len(argv) > 1 else "line"
    raw = _load(SHEET_CARDS_JSON) or {}
    # Computed straight from the freshly parsed sheet tabs so midday/EOD deltas do not
    # depend on the dashboard rebuild having finished.
    try:
        block = compute_cards(raw, date.today())
    except Exception as e:  # noqa: BLE001
        print(f"cards.py: could not compute cards block: {e}", file=sys.stderr)
        block = None
    if cmd == "line":
        print(pulse_line(block))
    elif cmd == "due":
        for g in (block or {}).get("dueItems", []):
            print(due_line(g))
    elif cmd == "health":
        issues = health_issues(block, bool(raw.get("present")))
        for i in issues:
            print(i)
        return 1 if issues else 0
    elif cmd == "delta":
        for ln in delta_lines(block, _load(LAST_SENT_JSON)):
            print(ln)
    elif cmd == "mark-sent":
        LAST_SENT_JSON.parent.mkdir(parents=True, exist_ok=True)
        LAST_SENT_JSON.write_text(json.dumps(snapshot(block)))
    else:
        print("usage: cards.py line|due|health|delta|mark-sent", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(_cli(sys.argv))
