"""
parse_hdfc_emails.py
=====================
Parses HDFC Bank transaction alert email snippets into structured rows for
the Bank_Transactions tab equivalent.

Input: JSON file (Gmail MCP search_threads output) at data/projects/_cache/hdfc_emails.json
Output: data/projects/sheet_bank_transactions.json

ACCOUNT FILTER — only the following First Rain business accounts are emitted.
Transactions from personal or unrelated accounts are silently dropped and
counted in meta.filteredWrongAccount.
  - 50200003890247  (HDFC Current Account, last-4: 0247)
  - 50200019750241  (HDFC OD Account,      last-4: 0241)

Senders handled:
  - alerts@hdfcbank.bank.in / alerts@hdfcbank.net  (txn alerts: debit/credit/UPI/cheque)
  - nachautoemailer@hdfcbank.bank.in               (NACH auto-debits: MF, EMI)
  - Inward.Remittances@hdfcbank.bank.in            (FCY inward credit advice)
  - fcyinward.disposal@hdfcbank.bank.in            (FCY disposal pending)

Senders dropped (non-transactional):
  - information@mailers.hdfcbank.bank.in           (system maintenance)
  - hdfcbanksmartstatement@hdfcbank.bank.in        (monthly statement)
  - customer.service@hdfcbank.bank.in              (home loan admin)
  - Emailintimation@hdfcbank.bank.in               (non-txn admin)
  - Enetadvicemailing@hdfcbank.net                 (payment advice — duplicates main alert)

Usage:
    python scripts/projects/parse_hdfc_emails.py data/projects/_cache/hdfc_emails.json

The Gmail MCP call (in /finance Step 3b) writes the input JSON; this script
reads it, parses, writes the output.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any

OUTPUT_PATH = Path("data/projects/sheet_bank_transactions.json")

# Senders we IGNORE (non-transactional)
NON_TXN_SENDERS = {
    "information@mailers.hdfcbank.bank.in",
    "hdfcbanksmartstatement@hdfcbank.bank.in",
    "customer.service@hdfcbank.bank.in",
    "Emailintimation@hdfcbank.bank.in",
    "emailintimation@hdfcbank.bank.in",
    "Enetadvicemailing@hdfcbank.net",
    "enetadvicemailing@hdfcbank.net",
}

# Subject prefixes / fragments that are NEVER transactional even though
# they come from alerts@hdfcbank.bank.in (admin / RM / maintenance pings)
NON_TXN_SUBJECT_FRAGMENTS = (
    "missed call from your hdfc bank",
    "skip the wait",
    "planned system maintenance",
    "scheduled downtime",
    "hdfc bank calls start",
    # Outward cross-border remittance confirmation from TradeQualityUnit@: the
    # downstream "beneficiary received it" notice. The INR debit was already
    # captured as a separate alert when the remittance was initiated, so this
    # is informational only — never a standalone transaction.
    "successful credit of your cross border remittance",
)

# Snippet fragments that mark a non-transactional admin notice
NON_TXN_SNIPPET_FRAGMENTS = (
    "successfully read secure usage tips",
    "accepted the terms",
    "mobilebanking app",
    "password reset",  # "Account update ... - NetBanking password reset"
)

# Bank sender domains — anything else (e.g. niloy@firstrain.co.in forwards)
# is silently dropped (counts as skipped, not unparseable)
BANK_SENDER_DOMAINS = ("hdfcbank.bank.in", "hdfcbank.net")

# First Rain business accounts — ONLY transactions from these last-4 digit
# suffixes are kept. All other accounts (personal savings, fixed deposits, etc.)
# are parsed but then dropped; counted in meta.filteredWrongAccount.
ALLOWED_ACCOUNTS = {"0247", "0241"}
# Full account numbers for reference:
#   50200003890247 → HDFC Current Account
#   50200019750241 → HDFC OD Account

# ---------- Regex patterns for snippet extraction ----------

AMOUNT = r"(?:Rs\.?\s*(?:INR\s*)?|INR\s*)([\d,]+(?:\.\d+)?)"
ACCOUNT = r"(?:account\s+(?:number\s+|ending\s+(?:with\s+)?))(?:XX+(\d{4})|XXXXXXXXXX(\d{4}))"
DATE_DDMMMYY = r"(\d{1,2})[-/](\w{3})[-/](\d{2,4})"
DATE_DDMMYY = r"(\d{1,2})[-/](\d{1,2})[-/](\d{2,4})"

# Pattern: "Rs.X has been debited from HDFC Bank Account Number XXXXXXXXXX4401 towards Y with UMRN ... on DD-Mon-YYYY"
P_NACH_DEBIT = re.compile(
    r"Rs\.?\s*([\d,]+\.?\d*)\s+has been debited from HDFC Bank Account Number XXXXXXXXXX(\d{4})"
    r"\s+towards\s+(.+?)\s+(?:with UMRN\s+(\S+)\s+)?on\s+" + DATE_DDMMMYY,
    re.IGNORECASE,
)

# Pattern: "Rs.X has been debited from account 4401 to VPA Y on DD-MM-YY"  (UPI)
P_UPI_DEBIT = re.compile(
    r"Rs\.?\s*([\d,]+\.?\d*)\s+has been debited from account\s+(\d{4})\s+to VPA\s+(\S+)\s+(.+?)\s+on\s+" + DATE_DDMMYY,
    re.IGNORECASE,
)

# Pattern: "Rs.X is debited from your account ending XXXX towards VPA Y (NAME) on DD-MM-YY"  (UPI alt)
P_UPI_DEBIT_V2 = re.compile(
    r"Rs\.?\s*([\d,]+\.?\d*)\s+is debited from your account ending\s+(\d{4})\s+towards VPA\s+(\S+)\s+\((.+?)\)\s+on\s+" + DATE_DDMMYY,
    re.IGNORECASE,
)

# Pattern: permissive UPI debit — "Rs.X (is) debited from (your) account ending NNNN [towards VPA Y]".
# Covers the alert variants that omit the (NAME) and/or the trailing date, which
# P_UPI_DEBIT_V2 requires. VPA is optional. Tried AFTER V2 so the richer match wins.
# (These are mostly personal-account 4401 spends — they parse, then route to the
# wrong-account filter so they stop showing up as "unparseable" noise.)
P_UPI_DEBIT_V3 = re.compile(
    r"Rs\.?\s*([\d,]+\.?\d*)\s+(?:is\s+)?debited from\s+(?:your\s+)?account ending\s+(\d{4})"
    r"(?:\s+towards VPA\s+(\S+))?",
    re.IGNORECASE,
)

# Pattern: "Rs. X has been deducted from your HDFC Bank account ending in XXNNNN for a transfer to payee Y via NEFT"
P_NEFT_DEBIT = re.compile(
    r"Rs\.?\s*(?:INR\s*)?([\d,]+\.?\d*)\s+has been deducted from your HDFC Bank account ending in XX(\d{4})"
    r"\s+for a transfer to payee\s+(.+?)\s+via NEFT",
    re.IGNORECASE,
)

# Pattern: "Rs. INR X is deducted from your account ending XXNNNN and added to ACH D- ... account on DD-MMM-YYYY"
P_ACH_DEBIT = re.compile(
    r"Rs\.?\s*(?:INR\s*)?([\d,]+\.?\d*)\s+is deducted from your account ending XX(\d{4})"
    r"\s+and added to\s+(.+?)\s+account on\s+" + DATE_DDMMMYY,
    re.IGNORECASE,
)

# Pattern: "Rs.INR X has been successfully added to your account ending XXNNNN from Y on DD-MMM-YYYY"
P_CREDIT = re.compile(
    r"Rs\.?\s*(?:INR\s*)?([\d,]+\.?\d*)\s+has been successfully added to your account ending XX(\d{4})"
    r"\s+from\s+(.+?)\s+on\s+" + DATE_DDMMMYY,
    re.IGNORECASE,
)

# Lenient fallback: same as P_CREDIT but no date — used when Gmail snippet
# truncates before the "on DD-MMM-YYYY" tail. Falls back to msg_date.
P_CREDIT_NO_DATE = re.compile(
    r"Rs\.?\s*(?:INR\s*)?([\d,]+\.?\d*)\s+has been successfully added to your account ending XX(\d{4})"
    r"\s+from\s+(.+?)(?:\s+on\b|$)",
    re.IGNORECASE,
)

# Pattern: "cheque no. NNNN has been successfully cleared, and an amount of Rs. INR X has been deducted from..."
P_CHEQUE = re.compile(
    r"cheque no\.?\s+(\d+)\s+has been successfully cleared,?\s+and an amount of\s+Rs\.?\s*(?:INR\s*)?([\d,]+\.?\d*)"
    r"\s+has been deducted from",
    re.IGNORECASE,
)

# Pattern (short form): "cheque no. NNNN has been successfully cleared, Rs. INR X deducted from XXNNNN".
# Same event as P_CHEQUE but without the "and an amount of ... has been deducted from"
# wording — the account tail is present, so capture it directly.
P_CHEQUE_SHORT = re.compile(
    r"cheque no\.?\s+(\d+)\s+has been successfully cleared,?\s+Rs\.?\s*(?:INR\s*)?([\d,]+\.?\d*)"
    r"\s+deducted from\s+XX(\d{4})",
    re.IGNORECASE,
)

# Pattern: account-update debit — "Rs. INR X deducted from XXNNNN - NARRATION".
# Covers expense/FD/internal-transfer alerts that carry a free-text narration after
# a dash (HP Laptop, Office Exp, FD Booked, Fund trf CA to OD, MahindraCar, etc.).
P_DEDUCT_NARRATION = re.compile(
    r"Rs\.?\s*(?:INR\s*)?([\d,]+\.?\d*)\s+deducted from\s+XX(\d{4})\s*[-–]\s*(.+)",
    re.IGNORECASE,
)

# Pattern: "Cheque of INR X has been successfully deposited in your A/c ending XXNNNN" (CREDIT).
# Gmail snippet frequently truncates the account tail (e.g. "XX0"), so the account
# group is 0-4 digits; cheque deposits land in the operating current account 0247,
# which we default to when the snippet is cut. Added 22 May 2026.
P_CHEQUE_DEPOSIT = re.compile(
    r"Cheque of\s+(?:Rs\.?\s*)?(?:INR\s*)?([\d,]+\.?\d*)\s+has been successfully deposited in your A/c ending XX(\d{0,4})",
    re.IGNORECASE,
)

# Pattern: "New Deposit Alert" template — HDFC's newer credit notification (added
# ~Jun 2026). Snippet: "You have received a credit in your HDFC Bank account.
# Details of the transaction: Amount received: INR X Account: XXNNNN Date:
# DD-MON-YYYY Reference Details: RTGS Cr-... | FD Redeem | FIRST RAIN EXH-..."
# 4+ credits to operating account 0247 were silently dropped before this fix.
P_NEW_DEPOSIT_ALERT = re.compile(
    r"You have received a credit.*?"
    r"Amount received:\s*INR\s*([\d,]+\.?\d*)\s*"
    r"Account:\s*XX(\d{4})\s*"
    r"Date:\s*(\d{1,2})[-/](\w{3})[-/](\d{2,4})\s*"
    r"Reference Details:\s*(.+?)(?:\s*$|<|\n)",
    re.IGNORECASE | re.DOTALL,
)

# Lenient fallback for the same template when snippet truncates before Reference
# Details. Date still required so we don't double-count balance pings.
P_NEW_DEPOSIT_ALERT_LITE = re.compile(
    r"You have received a credit.*?"
    r"Amount received:\s*INR\s*([\d,]+\.?\d*)\s*"
    r"Account:\s*XX(\d{4})",
    re.IGNORECASE | re.DOTALL,
)

# Manual cheque attribution — HDFC cheque-deposit alerts carry NO payer name, so
# the depositor must be confirmed manually. Keyed by (ISO date, amount) and by
# amount alone (fallback). Confirmed by Niloy.
CHEQUE_ATTRIBUTION = {
    ("2026-05-20", 454290.0): "Messung Systems",
    454290.0: "Messung Systems",
}

# Pattern (BALANCE-only ping, not txn): "Available balance in your account ending XXNNNN is Rs. INR X as on DD-MMM-YY"
P_BALANCE_ONLY = re.compile(
    r"Available balance in your account ending XX(\d{4})\s+is Rs\.?\s*(?:INR\s*)?([\d,]+\.?\d*)\s+as on\s+" + DATE_DDMMMYY,
    re.IGNORECASE,
)

# Pattern (BALANCE-only ping, short form): "Available balance in XXNNNN is Rs. INR X as on DD-MMM-YY"
P_BALANCE_ONLY_V2 = re.compile(
    r"Available balance in XX(\d{4})\s+is Rs\.?\s*(?:INR\s*)?([\d,]+\.?\d*)\s+as on\s+" + DATE_DDMMMYY,
    re.IGNORECASE,
)

# Pattern: FCY inward — pull from Subject because snippet often truncated
P_FCY_INWARD_SUBJECT = re.compile(
    r"INW\s+(\S+)\s+Debit\s+Cum\s+Credit\s+Advice",
    re.IGNORECASE,
)
P_FCY_DISPOSAL_SUBJECT = re.compile(
    r"DISPOSAL REQUIRED FOR FCY INWARD .*?For Account Number XXXXXXXXXX(\d{4}).*?(USD|EUR|GBP|AUD)\s+([\d,]+\.?\d*)\s+HDFC REF\.\s+(\S+)",
    re.IGNORECASE,
)

# Pattern: FCY snippet — "OSN_NO X INW_NO Y ... CUR USD FCY_AMT 11069.00 REMITER NAME ..."
P_FCY_SNIPPET = re.compile(
    r"FCY_AMT\s+([\d,]+\.?\d*).*?REMITER\s+(.+?)(?:\s+VALUE_DT|\s+OSN_NO|$)",
    re.IGNORECASE | re.DOTALL,
)


MONTH_MAP = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}


def _parse_date_dmy(d: str, m: str, y: str) -> date | None:
    try:
        day = int(d)
        if m.isdigit():
            month = int(m)
        else:
            month = MONTH_MAP.get(m.lower()[:3])
            if not month:
                return None
        year = int(y)
        if year < 100:
            year += 2000
        return date(year, month, day)
    except (ValueError, TypeError):
        return None


def _amt(s: str) -> float:
    return float(s.replace(",", ""))


# ---------------------------------------------------------------------------
# Task 7: generic fallback extractor + unknown-template logger
# ---------------------------------------------------------------------------

_UNKNOWN_TEMPLATES = Path("data/projects/_manual/hdfc_unknown_templates.txt")

# Permissive regexes for the fallback — looser than the named-template patterns
_FB_AMT_RE = re.compile(r"INR\s*([\d,]+(?:\.\d{1,2})?)", re.IGNORECASE)
_FB_ACCT_RE = re.compile(
    r"(?:account|a/c)\s*[:]?\s*(?:ending|ending in|no\.?)?\s*(?:XX)?(\d{4})",
    re.IGNORECASE,
)
_CREDIT_HINTS = ("credited", "moved into", "deposited", "received", "added to",
                 "credit", "has been added")
_DEBIT_HINTS = ("debited", "deducted", "withdrawn", "moved from",
                "transfer to", "towards", "debit", "has been deducted")


def _generic_hdfc_fallback(text: str | None) -> dict | None:
    """Permissive last-resort extractor for unrecognised HDFC alert templates.

    Returns a transaction dict with the SAME schema as parse_hdfc_email success
    paths, or None when the text is too ambiguous to extract safely.
    Only emits transactions for accounts in ALLOWED_ACCOUNTS (0247 / 0241),
    matching the main parser's account-filter policy.
    """
    if not text:
        return None
    amt_m = _FB_AMT_RE.search(text)
    acct_m = _FB_ACCT_RE.search(text)
    if not amt_m or not acct_m:
        return None
    account = acct_m.group(1)
    if account not in ALLOWED_ACCOUNTS:
        return None  # personal-account noise — same policy as the main parser
    low = text.lower()
    if any(h in low for h in _CREDIT_HINTS):
        direction = "credit"
    elif any(h in low for h in _DEBIT_HINTS):
        direction = "debit"
    else:
        return None  # direction ambiguous → let _log_unknown_template handle it
    return {
        "type": "generic_fallback",
        "date": None,           # no reliable date extraction in generic path
        "amount": _amt(amt_m.group(1)),
        "direction": direction,
        "account": account,
        "counterparty": "",
        "reference": "",
        "purpose": "Parsed by generic fallback — review recommended",
        "subject": "",
        "_sender": "",
    }


def _log_unknown_template(text: str | None) -> None:
    """Append a raw unrecognised alert snippet to the manual review queue (deduped).

    Writes to data/projects/_manual/hdfc_unknown_templates.txt, creating parent
    directories as needed.  Identical snippets are never written twice.
    """
    if not text:
        return
    snippet = " ".join(text.split())[:400]
    if not snippet:
        return
    _UNKNOWN_TEMPLATES.parent.mkdir(parents=True, exist_ok=True)
    existing = ""
    if _UNKNOWN_TEMPLATES.exists():
        existing = _UNKNOWN_TEMPLATES.read_text()
    if snippet in existing:
        return
    with _UNKNOWN_TEMPLATES.open("a") as fh:
        fh.write(snippet + "\n")


def _is_non_bank_sender(sender: str) -> bool:
    """True if sender is not from any HDFC bank domain (e.g. niloy@firstrain.co.in fwds)."""
    return not any(d in sender for d in BANK_SENDER_DOMAINS)


def _is_admin_notice(subject: str, snippet: str) -> bool:
    """True if subject or snippet matches a known non-transactional admin pattern."""
    sl = subject.lower()
    if any(frag in sl for frag in NON_TXN_SUBJECT_FRAGMENTS):
        return True
    snl = snippet.lower()
    if any(frag in snl for frag in NON_TXN_SNIPPET_FRAGMENTS):
        return True
    return False


def _is_internal_transfer(text: str) -> bool:
    """True if the narration is an internal OD<->CA own-account fund transfer.

    NARROW ON PURPOSE. Anchored on 'OD to CA' / 'CA to OD', or own name 'FIRST RAIN'
    with a transfer phrase. NEVER triggers on a bare 'fund transfer' / 'FT-' alone —
    clients pay by NEFT/RTGS fund transfer too and must stay classified as credits.
    """
    low = (text or "").lower()
    if "od to ca" in low or "ca to od" in low:
        return True
    if "first rain" in low and ("fund trf" in low or "fund transfer" in low or "ft-" in low):
        return True
    return False


def parse_hdfc_email(message: dict) -> dict | None:
    """Parse a single Gmail message dict. Returns a transaction dict or None.

    Thin wrapper over the template matcher: if the parsed credit/debit narration is
    an internal OD<->CA own-account transfer, reclassify it so it is excluded from
    Credits/Debits totals and never matched against client receivables/payables.
    """
    txn = _parse_hdfc_email_impl(message)
    if txn and txn.get("direction") in ("credit", "debit"):
        blob = f"{message.get('subject', '')} {message.get('snippet', '')}"
        if _is_internal_transfer(blob):
            txn["type"] = "INTERNAL_TRANSFER"
            txn["direction"] = "internal_transfer"
            txn["purpose"] = "Internal OD<->CA fund transfer (own account)"
    return txn


def _parse_hdfc_email_impl(message: dict) -> dict | None:
    """Parse a single Gmail message dict. Returns a transaction dict or None if non-txn."""
    sender = (message.get("sender") or "").lower()
    snippet = message.get("snippet") or ""
    subject = message.get("subject") or ""
    msg_date = (message.get("date") or "")[:10]  # YYYY-MM-DD slice from ISO

    if sender in NON_TXN_SENDERS:
        return None

    # Drop forwards from Niloy himself / any non-bank sender silently
    if _is_non_bank_sender(sender):
        return None

    # Drop known admin notices (RM missed call, maintenance, security tips, etc.)
    if _is_admin_notice(subject, snippet):
        return None

    # FCY inward (sender-based first)
    if "inward.remittances" in sender:
        m = P_FCY_INWARD_SUBJECT.search(subject)
        ref = m.group(1) if m else ""
        return {
            "type": "FCY_INWARD",
            "date": msg_date,
            "amount": 0.0,  # snippet doesn't have INR amount
            "direction": "credit",
            "account": "0247",  # FCY current account
            "counterparty": "",  # need to open thread to get details
            "reference": ref,
            "purpose": "FCY inward remittance — open thread for amount",
            "subject": subject,
            "_sender": sender,
            "_needsThreadFetch": True,
        }

    if "fcyinward.disposal" in sender:
        m = P_FCY_DISPOSAL_SUBJECT.search(subject)
        if m:
            account, ccy, amt, ref = m.groups()
            # Snippet may have remitter name
            rm = P_FCY_SNIPPET.search(snippet)
            remitter = rm.group(2).strip() if rm else ""
            return {
                "type": "FCY_DISPOSAL_PENDING",
                "date": msg_date,
                "amount": _amt(amt),
                "currency": ccy,
                "direction": "credit",
                "account": account,
                "counterparty": remitter,
                "reference": ref,
                "purpose": f"FCY {ccy} inward — disposal pending",
                "subject": subject,
                "_sender": sender,
            }

    # NACH auto-debit
    m = P_NACH_DEBIT.search(snippet)
    if m:
        amt, account, towards, umrn, dd, mm, yy = m.groups()
        txn_date = _parse_date_dmy(dd, mm, yy)
        return {
            "type": "NACH_DEBIT",
            "date": txn_date.isoformat() if txn_date else msg_date,
            "amount": _amt(amt),
            "direction": "debit",
            "account": account,
            "counterparty": towards.strip(),
            "reference": umrn or "",
            "purpose": "NACH auto-debit",
            "subject": subject,
            "_sender": sender,
        }

    # UPI debit
    m = P_UPI_DEBIT.search(snippet)
    if m:
        amt, account, vpa, narration, dd, mm, yy = m.groups()
        txn_date = _parse_date_dmy(dd, mm, yy)
        return {
            "type": "UPI_DEBIT",
            "date": txn_date.isoformat() if txn_date else msg_date,
            "amount": _amt(amt),
            "direction": "debit",
            "account": account,
            "counterparty": narration.strip(),
            "reference": vpa,
            "purpose": "UPI payment",
            "subject": subject,
            "_sender": sender,
        }

    # UPI debit v2 ("is debited... towards VPA... (NAME)")
    m = P_UPI_DEBIT_V2.search(snippet)
    if m:
        amt, account, vpa, narration, dd, mm, yy = m.groups()
        txn_date = _parse_date_dmy(dd, mm, yy)
        return {
            "type": "UPI_DEBIT",
            "date": txn_date.isoformat() if txn_date else msg_date,
            "amount": _amt(amt),
            "direction": "debit",
            "account": account,
            "counterparty": narration.strip(),
            "reference": vpa,
            "purpose": "UPI payment",
            "subject": subject,
            "_sender": sender,
        }

    # UPI debit v3 — permissive variant (no required (NAME)/date; VPA optional)
    m = P_UPI_DEBIT_V3.search(snippet)
    if m:
        amt, account, vpa = m.groups()
        return {
            "type": "UPI_DEBIT",
            "date": msg_date,
            "amount": _amt(amt),
            "direction": "debit",
            "account": account,
            "counterparty": (vpa or "").strip(),
            "reference": vpa or "",
            "purpose": "UPI payment",
            "subject": subject,
            "_sender": sender,
        }

    # NEFT outward ("deducted from your HDFC Bank account ending in XXNNNN for a transfer to payee Y via NEFT")
    m = P_NEFT_DEBIT.search(snippet)
    if m:
        amt, account, payee = m.groups()
        return {
            "type": "NEFT_DEBIT",
            "date": msg_date,
            "amount": _amt(amt),
            "direction": "debit",
            "account": account,
            "counterparty": payee.strip(),
            "reference": "",
            "purpose": "NEFT outward transfer",
            "subject": subject,
            "_sender": sender,
        }

    # ACH debit
    m = P_ACH_DEBIT.search(snippet)
    if m:
        amt, account, towards, dd, mm, yy = m.groups()
        txn_date = _parse_date_dmy(dd, mm, yy)
        return {
            "type": "ACH_DEBIT",
            "date": txn_date.isoformat() if txn_date else msg_date,
            "amount": _amt(amt),
            "direction": "debit",
            "account": account,
            "counterparty": towards.strip(),
            "reference": "",
            "purpose": "ACH debit",
            "subject": subject,
            "_sender": sender,
        }

    # "New Deposit Alert" template (Jun-2026 onwards) — checked BEFORE legacy
    # P_CREDIT because the snippet phrasing is completely different and the
    # legacy regex would silently not match.
    m = P_NEW_DEPOSIT_ALERT.search(snippet)
    if m:
        amt, account, dd, mm, yy, ref_details = m.groups()
        txn_date = _parse_date_dmy(dd, mm, yy)
        ref_clean = ref_details.strip().rstrip("-").rstrip(",")
        rl = ref_clean.lower()
        purpose = "Credit"
        counterparty = ref_clean
        if "rtgs" in rl or "neft" in rl:
            purpose = "Fund Transfer credit"
            # Strip "RTGS Cr-IFSC-" prefix to expose payer name
            m2 = re.search(r"(?:RTGS|NEFT)\s+Cr-[A-Z0-9]+-(.+)", ref_clean, re.IGNORECASE)
            if m2:
                counterparty = m2.group(1).strip()
        elif "fd redeem" in rl or "fd matur" in rl:
            purpose = "FD redemption"
        elif "ppfas" in rl or "mutual fund" in rl or rl.startswith("mf "):
            purpose = "MF redemption"
        elif "first rain" in rl:
            purpose = "Internal transfer (self)"
        return {
            "type": "CREDIT",
            "date": txn_date.isoformat() if txn_date else msg_date,
            "amount": _amt(amt),
            "direction": "credit",
            "account": account,
            "counterparty": counterparty,
            "reference": ref_clean,
            "purpose": purpose,
            "subject": subject,
            "_sender": sender,
        }

    # Credit (FT/Salary/etc)
    m = P_CREDIT.search(snippet)
    if m:
        amt, account, source, dd, mm, yy = m.groups()
        txn_date = _parse_date_dmy(dd, mm, yy)
        purpose = "Credit"
        src_lower = source.lower()
        if "ft-" in src_lower or "ft " in src_lower:
            purpose = "Fund Transfer credit"
        elif "salary" in src_lower or "remune" in src_lower:
            purpose = "Director remuneration / salary"
        elif "ppfas" in src_lower or "mutual fund" in src_lower or "mf " in src_lower:
            purpose = "MF redemption"
        return {
            "type": "CREDIT",
            "date": txn_date.isoformat() if txn_date else msg_date,
            "amount": _amt(amt),
            "direction": "credit",
            "account": account,
            "counterparty": source.strip(),
            "reference": "",
            "purpose": purpose,
            "subject": subject,
            "_sender": sender,
        }

    # Cheque cleared
    m = P_CHEQUE.search(snippet)
    if m:
        cheque_no, amt = m.groups()
        return {
            "type": "CHEQUE_CLEARED",
            "date": msg_date,
            "amount": _amt(amt),
            "direction": "debit",
            "account": "",  # not in snippet
            "counterparty": "",
            "reference": f"Cheque {cheque_no}",
            "purpose": "Cheque cleared",
            "subject": subject,
            "_sender": sender,
        }

    # Cheque cleared (short form: "...cleared, Rs. INR X deducted from XXNNNN")
    m = P_CHEQUE_SHORT.search(snippet)
    if m:
        cheque_no, amt, account = m.groups()
        return {
            "type": "CHEQUE_CLEARED",
            "date": msg_date,
            "amount": _amt(amt),
            "direction": "debit",
            "account": account,
            "counterparty": "",
            "reference": f"Cheque {cheque_no}",
            "purpose": "Cheque cleared",
            "subject": subject,
            "_sender": sender,
        }

    # Account-update debit with free-text narration ("Rs. INR X deducted from XXNNNN - NARRATION").
    # FD bookings move cash to an own fixed deposit (treasury), so they are flagged
    # internal_transfer to keep them out of the operating-debit / burn totals. The
    # parse_hdfc_email wrapper separately reclassifies CA<->OD narrations.
    m = P_DEDUCT_NARRATION.search(snippet)
    if m:
        amt, account, narration = m.groups()
        narration = narration.strip()
        nlow = narration.lower()
        is_fd = "fd booked" in nlow or "fd booking" in nlow or nlow.startswith("fd ")
        return {
            "type": "FD_BOOKING" if is_fd else "DEBIT",
            "date": msg_date,
            "amount": _amt(amt),
            "direction": "internal_transfer" if is_fd else "debit",
            "account": account,
            "counterparty": narration,
            "reference": "",
            "purpose": "FD booked (own treasury)" if is_fd else "Account debit",
            "subject": subject,
            "_sender": sender,
        }

    # Cheque deposit (credit into account) — snippet often truncates the account,
    # so default to the operating current account 0247 when fewer than 4 digits parse.
    m = P_CHEQUE_DEPOSIT.search(snippet)
    if m:
        amt, acct = m.groups()
        amt_val = _amt(amt)
        payer = CHEQUE_ATTRIBUTION.get((msg_date, amt_val)) or CHEQUE_ATTRIBUTION.get(amt_val)
        return {
            "type": "CHEQUE_DEPOSIT",
            "date": msg_date,
            "amount": amt_val,
            "direction": "credit",
            "account": acct if (acct and len(acct) == 4) else "0247",
            "counterparty": payer or "Cheque deposit",
            "reference": "",
            "purpose": "Cheque deposit",
            "subject": subject,
            "_sender": sender,
        }

    # "New Deposit Alert" LITE — when snippet truncates before "Reference Details"
    m = P_NEW_DEPOSIT_ALERT_LITE.search(snippet)
    if m:
        amt, account = m.groups()
        return {
            "type": "CREDIT",
            "date": msg_date,
            "amount": _amt(amt),
            "direction": "credit",
            "account": account,
            "counterparty": "",
            "reference": "",
            "purpose": "Credit",
            "subject": subject,
            "_sender": sender,
            "_dateFromMsgHeader": True,
        }

    # Credit fallback: snippet truncated before the date — use msg_date
    m = P_CREDIT_NO_DATE.search(snippet)
    if m:
        amt, account, source = m.groups()
        purpose = "Credit"
        src_lower = source.lower()
        if "ft-" in src_lower or "ft " in src_lower:
            purpose = "Fund Transfer credit"
        elif "salary" in src_lower or "remune" in src_lower:
            purpose = "Director remuneration / salary"
        elif "ppfas" in src_lower or "mutual fund" in src_lower or "mf " in src_lower:
            purpose = "MF redemption"
        return {
            "type": "CREDIT",
            "date": msg_date,
            "amount": _amt(amt),
            "direction": "credit",
            "account": account,
            "counterparty": source.strip(),
            "reference": "",
            "purpose": purpose,
            "subject": subject,
            "_sender": sender,
            "_dateFromMsgHeader": True,  # snippet was truncated
        }

    # Balance-only ping FALLBACK — try this last so we never mask a txn
    if "available balance" in snippet.lower():
        m = P_BALANCE_ONLY.search(snippet) or P_BALANCE_ONLY_V2.search(snippet)
        if m:
            account, balance, dd, mm, yy = m.groups()
            txn_date = _parse_date_dmy(dd, mm, yy)
            return {
                "type": "BALANCE_SNAPSHOT",
                "date": txn_date.isoformat() if txn_date else msg_date,
                "amount": _amt(balance),
                "direction": "snapshot",
                "account": account,
                "counterparty": "",
                "reference": "",
                "purpose": "Daily balance ping",
                "subject": subject,
                "_sender": sender,
            }

    # No specific template matched — try the permissive fallback before giving up.
    _blob = f"{subject} {snippet}"
    _fallback = _generic_hdfc_fallback(_blob)
    if _fallback is not None:
        # Preserve the envelope fields the main parser always populates
        _fallback["date"] = msg_date
        _fallback["subject"] = subject
        _fallback["_sender"] = sender
        return _fallback
    _log_unknown_template(_blob)
    return None  # Unrecognized — logged to _manual/hdfc_unknown_templates.txt


def parse_threads(threads_json: dict) -> dict:
    threads = threads_json.get("threads", []) if isinstance(threads_json, dict) else []
    transactions = []
    warnings = []
    skipped_non_txn = 0
    filtered_account = 0  # parsed OK but wrong account

    for thread in threads:
        for msg in thread.get("messages", []):
            sender = (msg.get("sender") or "").lower()
            subject = msg.get("subject") or ""
            snippet = msg.get("snippet") or ""
            txn = parse_hdfc_email(msg)
            if txn:
                acct = txn.get("account", "")
                if acct in ALLOWED_ACCOUNTS:
                    transactions.append(txn)
                else:
                    # Parsed successfully but belongs to a personal/unrelated account
                    filtered_account += 1
            elif (
                sender in NON_TXN_SENDERS
                or _is_non_bank_sender(sender)
                or _is_admin_notice(subject, snippet)
            ):
                skipped_non_txn += 1
            else:
                warnings.append({
                    "id": msg.get("id"),
                    "sender": msg.get("sender"),
                    "subject": msg.get("subject"),
                    "snippet": snippet[:120],
                    "reason": "no_pattern_matched",
                })

    # Dedupe pass 1: exact match on (date, amount, account, type, counterparty)
    seen = set()
    unique_transactions = []
    for txn in transactions:
        key = (txn["date"], txn["amount"], txn["account"], txn["type"], txn.get("counterparty", ""))
        if key in seen:
            continue
        seen.add(key)
        unique_transactions.append(txn)

    # Dedupe pass 2: HDFC sends BOTH a NACH alert (from nachautoemailer@) AND
    # an ACH alert (from alerts@) for the same underlying SIP/EMI debit.
    # Collapse NACH+ACH pairs sharing (date, amount, account). Keep NACH —
    # it carries the UMRN reference, which is more useful for reconciliation.
    nach_keys = {
        (t["date"], t["amount"], t["account"])
        for t in unique_transactions
        if t["type"] == "NACH_DEBIT"
    }
    deduped = [
        t for t in unique_transactions
        if not (
            t["type"] == "ACH_DEBIT"
            and (t["date"], t["amount"], t["account"]) in nach_keys
        )
    ]
    nach_ach_collapsed = len(unique_transactions) - len(deduped)
    unique_transactions = deduped

    # Sort by date desc
    unique_transactions.sort(key=lambda t: t["date"], reverse=True)

    # Compute totals (excluding balance snapshots and FCY entries — those are
    # in foreign currency and would corrupt INR sums until FX conversion is wired)
    FCY_TYPES = ("FCY_INWARD", "FCY_DISPOSAL_PENDING")
    total_credits = sum(
        t["amount"] for t in unique_transactions
        if t.get("direction") == "credit" and t.get("type") not in FCY_TYPES
    )
    total_debits = sum(t["amount"] for t in unique_transactions if t.get("direction") == "debit")
    txn_count = sum(
        1 for t in unique_transactions
        if t.get("direction") in ("credit", "debit") and t.get("type") not in FCY_TYPES
    )
    fcy_pending = [t for t in unique_transactions if t.get("type") in FCY_TYPES]
    balance_snapshots = [t for t in unique_transactions if t.get("type") == "BALANCE_SNAPSHOT"]
    latest_balance = balance_snapshots[0] if balance_snapshots else None

    return {
        "transactions": unique_transactions,
        "totals": {
            "credits": total_credits,
            "debits": total_debits,
            "net": total_credits - total_debits,
            "transactionCount": txn_count,
            "fcyPendingCount": len(fcy_pending),
        },
        "fcyPending": fcy_pending,
        "latestBalance": latest_balance,
        "meta": {
            "count": len(unique_transactions),
            "allowedAccounts": sorted(ALLOWED_ACCOUNTS),
            "filteredWrongAccount": filtered_account,
            "rawDuplicatesRemoved": len(transactions) - len(unique_transactions),
            "nachAchPairsCollapsed": nach_ach_collapsed,
            "skippedNonTransactional": skipped_non_txn,
            "unparseableCount": len(warnings),
            "read_at": datetime.now().astimezone().isoformat(),
            "warnings": warnings[:20],  # first 20 only — full list bloats JSON
        },
    }


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(
            "ERROR: missing input JSON path.\n"
            "Usage: python scripts/projects/parse_hdfc_emails.py <path_to_threads.json>\n"
            "The input file is the Gmail MCP search_threads output saved by /finance Step 3b.",
            file=sys.stderr,
        )
        return 1
    inp = Path(argv[1])
    if not inp.exists():
        print(f"ERROR: {inp} not found", file=sys.stderr)
        return 1

    threads_json = json.load(open(inp))
    result = parse_threads(threads_json)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(result, f, indent=2, default=str)

    meta = result["meta"]
    totals = result["totals"]
    print(
        f"✓ {meta['count']} unique transactions parsed "
        f"({totals['transactionCount']} txns + {meta['count'] - totals['transactionCount']} balance snapshots)"
    )
    print(f"  Accounts kept: {meta['allowedAccounts']}  (0247 = Current, 0241 = OD)")
    print(f"  Filtered wrong account: {meta['filteredWrongAccount']}")
    print(f"  Credits: ₹{totals['credits']:,.2f}  Debits: ₹{totals['debits']:,.2f}  Net: ₹{totals['net']:,.2f}")
    print(f"  Skipped non-txn: {meta['skippedNonTransactional']}  Unparseable: {meta['unparseableCount']}")
    if meta["unparseableCount"]:
        print(f"  ⚠ First few unparseable senders: {[w['sender'] for w in meta['warnings'][:5]]}")
    print(f"→ {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
