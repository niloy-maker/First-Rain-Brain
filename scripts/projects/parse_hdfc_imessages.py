"""
parse_hdfc_imessages.py
=======================
Reads HDFC bank SMS transaction alerts from macOS Messages database (chat.db).
Works alongside parse_hdfc_emails.py — provides real-time SMS as a
secondary/validation source for credits and debits.

HDFC SMS arrives on phone before the email alert lands in Gmail.
This script catches credits that Gmail hasn't reported yet.

Output: data/projects/_cache/hdfc_imessages.json
"""

import sqlite3
import re
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = Path.home() / "Library/Messages/chat.db"
OUTPUT_PATH = Path("data/projects/_cache/hdfc_imessages.json")
DAYS_BACK = 30

# BYPASS MECHANISM (added 24 May 2026) ----------------------------------------
# Manual paste file: when iPhone->Mac SMS sync is down, raw HDFC SMS text pasted
# here is parsed with the same logic and merged in. See file header for format.
MANUAL_PATH = Path("data/projects/_manual/hdfc_sms_manual.txt")
# If the newest message of ANY kind in chat.db is older than this, the local DB
# has almost certainly stopped syncing from the iPhone (the phone receives OTPs,
# promos, etc. constantly). Below threshold = 'live'; above = 'stale'.
STALE_THRESHOLD_HOURS = 36
# Bank-sender feed: HDFC transaction alerts normally arrive within ~a day on any
# active business account. If the newest HDFC *bank-sender* SMS is older than this
# while the phone feed is otherwise live, the bank route is likely being filtered or
# iCloud sync is paused — even though promo/OTP SMS keep the overall feed "live".
BANK_STALE_THRESHOLD_HOURS = 30
# -----------------------------------------------------------------------------

# Only these two accounts are business accounts (per decision-log 24 Apr 2026)
ALLOWED_ACCOUNTS = {"0247", "0241"}

# Authorised HDFC sender ID prefixes (per Niloy's decision 24 May 2026)
# chat.db stores sender IDs with a routing suffix, e.g. 'HDFCBK-S(smsft_fi)'
# Use startswith() matching — the prefix is stable, the suffix varies by carrier route.
# HDFCBK-T = HDFC Bank transactional alerts
# HDFCBK-S = HDFC Bank service/credit alerts
# HDFCMF-S = HDFC Mutual Fund
# HDFCBN-S = HDFC Bank Net Banking notifications
HDFC_SENDER_PREFIXES = (
    "HDFCBK-T", "HDFCBK-S", "HDFCMF-S", "HDFCBN-S",
    # Indian carrier VM- prefix variants
    "VM-HDFCBK-T", "VM-HDFCBK-S", "VM-HDFCMF-S", "VM-HDFCBN-S",
)

APPLE_EPOCH = 978307200  # seconds between Unix epoch (1970) and Apple epoch (2001)


def parse_amount(text):
    """Extract INR amount from HDFC SMS text. Returns float or None."""
    patterns = [
        r'INR\s*([\d,]+\.?\d*)',
        r'Rs\.?\s*([\d,]+\.?\d*)',
        r'₹\s*([\d,]+\.?\d*)',
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            try:
                return float(m.group(1).replace(',', ''))
            except ValueError:
                pass
    return None


def parse_account(text):
    """
    Extract 4-digit account ending from HDFC SMS.
    Returns the account string (e.g. '0247') or None.
    """
    # Explicit account markers
    m = re.search(
        r'(?:A/c|Ac|Acct|account|Acct\.)\s*(?:No\.?\s*)?(?:XX[- ]?|ending\s*)?(\d{4})\b',
        text, re.IGNORECASE
    )
    if m:
        return m.group(1)
    # Fall back: look for bare 0247 / 0241
    for acct in ALLOWED_ACCOUNTS:
        if acct in text:
            return acct
    return None


def is_internal_transfer(text):
    """True if the narration is an internal OD<->CA own-account fund transfer.

    NARROW ON PURPOSE. Anchored on the unambiguous own-account markers:
      - 'OD to CA' / 'CA to OD'  (appears in both legs of an OD draw), or
      - own name 'FIRST RAIN' together with a fund-transfer phrase.
    It must NEVER trigger on a bare 'fund transfer' / 'FT-' alone — clients pay by
    NEFT/RTGS fund transfer too, and those must stay classified as real credits.
    """
    low = (text or "").lower()
    if "od to ca" in low or "ca to od" in low:
        return True
    if "first rain" in low and ("fund trf" in low or "fund transfer" in low or "ft-" in low):
        return True
    return False


def parse_txn_type(text):
    """Return 'internal_transfer', 'credit', 'debit', or 'unknown'.

    HDFC SMS uses 'deposited' for inbound credits (RTGS/NEFT/transfers),
    'credited' for some older templates, and 'debited'/'deducted' for outflows.
    Internal OD<->CA transfers also say 'deposited'/'debited', so they MUST be
    checked first (own money moving between 0247 and 0241 — not income/expense).
    """
    if is_internal_transfer(text):
        return 'internal_transfer'
    low = text.lower()
    if any(w in low for w in ('deposited', 'credited', 'credit received', 'received in')):
        return 'credit'
    if any(w in low for w in ('debited', 'deducted', 'debited from', 'paid via')):
        return 'debit'
    return 'unknown'


def parse_counterparty(text):
    """
    Try to extract counterparty name from HDFC SMS.
    Returns string or None.
    """
    patterns = [
        # HDFC RTGS/NEFT credit: "RTGS Cr-KKBK0000958-MESSUNG SYSTEMS PRIVATE LIMITED-..."
        # The sender name is the segment between the 2nd and 3rd dashes
        r'(?:RTGS|NEFT)\s+Cr-[^-]+-([^-]{3,60})-',
        # HDFC internal fund transfer: "for FIRST RAIN EXH-Fund trf CA to OD"
        r'for\s+([A-Z][A-Z\s]{3,40}?)(?:\.|$|-Fund\b)',
        # HDFC MF/vendor narration: "towards MF Utilities India Pvt Ltd"
        r'towards\s+([A-Za-z][A-Za-z\s&.,()]{3,50?})(?:\s+UMRN|\.|$)',
        # Name in parentheses
        r'\(([A-Z][A-Za-z\s&.,-]{2,40})\)',
        r'payee\s+([A-Z][A-Za-z\s&.,-]{2,40?})(?:\s+via|\s+on|\.|$)',
        r'beneficiary\s+([A-Z][A-Za-z\s&.,-]{2,40?})(?:\s+via|\s+on|\.|$)',
        r'from\s+([A-Z][A-Za-z\s&.,-]{2,40?})\s+(?:via|on|to)',
        r'to\s+([A-Z][A-Za-z\s&.,-]{2,40?})\s+(?:via|on)',
    ]
    for p in patterns:
        m = re.search(p, text)
        if m:
            name = m.group(1).strip().rstrip('.,')
            if len(name) > 2:
                return name
    return None


def query_hdfc_messages():
    """
    Query chat.db for messages likely to be HDFC transaction alerts.
    Searches by text content — does not require knowing HDFC sender numbers.
    """
    if not DB_PATH.exists():
        print(f"  ⚠ Messages DB not found at {DB_PATH} — skipping iMessage parse", file=sys.stderr)
        return []

    cutoff_ts = datetime.now() - timedelta(days=DAYS_BACK)
    # Apple timestamps are nanoseconds from 2001-01-01
    cutoff_apple_ns = (cutoff_ts.timestamp() - APPLE_EPOCH) * 1_000_000_000

    try:
        conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        cur.execute("""
            SELECT
                m.ROWID            AS message_id,
                m.text             AS content,
                datetime(m.date / 1000000000 + 978307200, 'unixepoch', 'localtime') AS date_str,
                m.date             AS apple_date,
                h.id               AS sender,
                m.is_from_me
            FROM message m
            INNER JOIN handle h ON h.ROWID = m.handle_id
            WHERE m.date >= ?
              AND m.is_from_me  = 0
              AND m.item_type   = 0
              AND m.is_audio_message = 0
              AND m.text IS NOT NULL
              AND m.text != ''
              AND (
                  -- Authorised sender ID prefixes (chat.db appends routing suffix like '(smsft_fi)')
                  h.id LIKE 'HDFCBK-T%'
               OR h.id LIKE 'HDFCBK-S%'
               OR h.id LIKE 'HDFCMF-S%'
               OR h.id LIKE 'HDFCBN-S%'
               OR h.id LIKE 'VM-HDFCBK-T%'
               OR h.id LIKE 'VM-HDFCBK-S%'
               OR h.id LIKE 'VM-HDFCMF-S%'
               OR h.id LIKE 'VM-HDFCBN-S%'
                  -- Text fallback: catches future format changes and unlabelled forwards
               OR m.text LIKE '%0247%'
               OR m.text LIKE '%0241%'
               OR (m.text LIKE '%HDFC%'
                   AND (   m.text LIKE '%credit%'
                        OR m.text LIKE '%debit%'
                        OR m.text LIKE '%INR%'))
              )
            ORDER BY m.date DESC
            LIMIT 200
        """, (cutoff_apple_ns,))

        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows

    except sqlite3.OperationalError as e:
        # Common cause: Full Disk Access not granted to Claude Code
        print(f"  ⚠ DB read error (check Full Disk Access for Claude Code): {e}", file=sys.stderr)
        return []
    except Exception as e:
        print(f"  ⚠ Unexpected error querying Messages DB: {e}", file=sys.stderr)
        return []


def parse_messages(rows):
    """Parse raw DB rows into structured transaction objects."""
    transactions = []
    seen = set()

    for row in rows:
        text = row.get('content') or ''
        if not text.strip():
            continue

        # Drop rows where sender is not an authorised HDFC sender prefix
        # chat.db appends a routing suffix (e.g. 'HDFCBK-S(smsft_fi)') — use startswith
        sender = row.get('sender', '')
        if sender and not any(sender.startswith(p) for p in HDFC_SENDER_PREFIXES):
            continue

        amount = parse_amount(text)
        account = parse_account(text)
        txn_type = parse_txn_type(text)
        counterparty = parse_counterparty(text)

        # Must have amount and a parseable direction
        if not amount or txn_type == 'unknown':
            continue

        # Enforce business-account filter
        if account and account not in ALLOWED_ACCOUNTS:
            continue

        date_str = row.get('date_str', '')
        # Deduplicate by (minute, amount, direction)
        dedup_key = (date_str[:16], amount, txn_type)
        if dedup_key in seen:
            continue
        seen.add(dedup_key)

        transactions.append({
            'source': 'imessage_sms',
            'message_id': row.get('message_id'),
            'date': date_str,
            'sender': row.get('sender', ''),
            'account': account or 'unknown',
            'type': txn_type,           # 'credit' | 'debit'
            'amount': amount,
            'counterparty': counterparty,
            'raw_text': text[:400],
        })

    return transactions


def cross_reference_with_gmail(transactions):
    """
    Optionally load Gmail-sourced bank transactions and annotate matches.
    Looks for data/projects/sheet_bank_transactions.json written by parse_hdfc_emails.py.
    """
    gmail_path = Path("data/projects/sheet_bank_transactions.json")
    if not gmail_path.exists():
        return transactions

    try:
        gmail_data = json.loads(gmail_path.read_text())
        gmail_txns = gmail_data.get('transactions', [])
    except Exception:
        return transactions

    for sms_txn in transactions:
        sms_date = sms_txn.get('date', '')[:10]   # YYYY-MM-DD
        sms_amount = sms_txn.get('amount', 0)
        sms_type = sms_txn.get('type')

        matched = False
        for g in gmail_txns:
            g_date = (g.get('date') or g.get('timestamp') or '')[:10]
            g_amount = float(g.get('amount', 0))
            g_type = g.get('type', '')

            date_close = abs((
                datetime.strptime(sms_date, '%Y-%m-%d') -
                datetime.strptime(g_date, '%Y-%m-%d')
            ).days) <= 1 if sms_date and g_date else False

            amount_close = abs(sms_amount - g_amount) / max(sms_amount, 1) < 0.05  # ±5%

            if date_close and amount_close and sms_type == g_type:
                matched = True
                break

        sms_txn['gmail_confirmed'] = matched
        sms_txn['confidence'] = 'high' if matched else 'sms_only'

    return transactions


def classify_feed(h_any, h_hdfc, threshold=STALE_THRESHOLD_HOURS,
                  bank_threshold=BANK_STALE_THRESHOLD_HOURS):
    """Pure decision: turn message ages into feed statuses. No I/O — unit-testable.

    Returns (feed_status, bank_feed_status, bank_stale_but_phone_live):
      - feed_status      : 'live'|'stale'|'unknown' — the OVERALL phone feed (any sender)
      - bank_feed_status : 'live'|'stale'|'unknown' — the HDFC bank-sender feed specifically
      - bank_stale_but_phone_live : True when the phone feed looks live but the bank feed
        is stale/unknown — the false-confidence trap (filtering or paused sync). Thresholds
        are exclusive: an age exactly equal to the threshold is still 'live'.
    """
    if h_any is None:
        feed_status = 'unknown'
    elif h_any > threshold:
        feed_status = 'stale'
    else:
        feed_status = 'live'

    if h_hdfc is None:
        bank_feed_status = 'unknown'
    elif h_hdfc > bank_threshold:
        bank_feed_status = 'stale'
    else:
        bank_feed_status = 'live'

    bank_stale_but_phone_live = (feed_status == 'live' and bank_feed_status in ('stale', 'unknown'))
    return feed_status, bank_feed_status, bank_stale_but_phone_live


def compute_feed_health():
    """
    Determine whether the local Messages DB is still syncing from the iPhone.

    The phone receives many messages daily (OTPs, promos, iMessages). If the
    newest message of ANY kind in chat.db is older than STALE_THRESHOLD_HOURS,
    the local DB has almost certainly stopped syncing — so the SMS route is DOWN
    and the syncs must rely on the Gmail HDFC email alerts (Mac-independent) plus
    any manual bypass entries.

    Returns a dict: feed_status ('live'|'stale'|'unknown'), last message dates,
    and hours since each.
    """
    base = {
        'feed_status': 'unknown',
        'last_any_msg_date': None,
        'last_hdfc_sms_date': None,
        'hours_since_any': None,
        'hours_since_hdfc': None,
        'stale_threshold_hours': STALE_THRESHOLD_HOURS,
    }
    if not DB_PATH.exists():
        base['reason'] = 'chat.db not found'
        return base
    try:
        conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
        cur = conn.cursor()
        cur.execute(
            "SELECT datetime(MAX(date)/1000000000+978307200,'unixepoch','localtime') FROM message"
        )
        last_any = cur.fetchone()[0]
        like_clauses = " OR ".join(["h.id LIKE ?"] * len(HDFC_SENDER_PREFIXES))
        params = [p + '%' for p in HDFC_SENDER_PREFIXES]
        cur.execute(
            f"""SELECT datetime(MAX(m.date)/1000000000+978307200,'unixepoch','localtime')
                FROM message m INNER JOIN handle h ON h.ROWID = m.handle_id
                WHERE {like_clauses}""",
            params,
        )
        last_hdfc = cur.fetchone()[0]
        conn.close()
    except Exception as e:
        base['reason'] = str(e)
        return base

    now = datetime.now()

    def hours_since(dt_str):
        if not dt_str:
            return None
        try:
            delta = now - datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
            return round(delta.total_seconds() / 3600, 1)
        except Exception:
            return None

    h_any = hours_since(last_any)
    h_hdfc = hours_since(last_hdfc)

    status, bank_status, bank_stale_but_phone_live = classify_feed(h_any, h_hdfc)

    base.update({
        'feed_status': status,
        'bank_feed_status': bank_status,
        'bank_stale_but_phone_live': bank_stale_but_phone_live,
        'bank_stale_threshold_hours': BANK_STALE_THRESHOLD_HOURS,
        'last_any_msg_date': last_any,
        'last_hdfc_sms_date': last_hdfc,
        'hours_since_any': h_any,
        'hours_since_hdfc': h_hdfc,
    })
    return base


def load_manual_entries():
    """
    BYPASS: read manually-pasted HDFC SMS from MANUAL_PATH.

    Use this when iPhone->Mac SMS sync is down: paste the raw HDFC SMS text into
    data/projects/_manual/hdfc_sms_manual.txt. Each SMS is a block (blank-line
    separated). Lines starting with '#' are ignored. Optionally prefix a block
    with a timestamp like [2026-05-24 14:30]; otherwise the current time is used.

    Parsed with the SAME amount/account/type/counterparty logic as real SMS and
    tagged source='manual_paste' so they flow into the dashboard and the syncs.
    """
    if not MANUAL_PATH.exists():
        return []
    try:
        raw = MANUAL_PATH.read_text()
    except Exception:
        return []

    entries = []
    seen = set()
    for block in re.split(r'\n\s*\n', raw):
        lines = [ln for ln in block.splitlines()
                 if ln.strip() and not ln.strip().startswith('#')]
        if not lines:
            continue
        text = " ".join(lines).strip()
        if not text:
            continue

        # Optional leading [date] / [date time] prefix
        date_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        m = re.match(r'\[(\d{4}-\d{2}-\d{2}(?:[ T]\d{2}:\d{2})?)\]\s*(.*)', text)
        if m:
            d = m.group(1).replace('T', ' ')
            if len(d) == 10:          # date only
                d += ' 00:00'
            date_str = d + ':00'      # add seconds
            text = m.group(2)

        amount = parse_amount(text)
        account = parse_account(text)
        txn_type = parse_txn_type(text)
        counterparty = parse_counterparty(text)

        if not amount or txn_type == 'unknown':
            continue
        if account and account not in ALLOWED_ACCOUNTS:
            continue

        dedup_key = (date_str[:16], amount, txn_type)
        if dedup_key in seen:
            continue
        seen.add(dedup_key)

        entries.append({
            'source': 'manual_paste',
            'message_id': None,
            'date': date_str,
            'sender': 'manual_bypass',
            'account': account or 'unknown',
            'type': txn_type,
            'amount': amount,
            'counterparty': counterparty,
            'raw_text': text[:400],
        })
    return entries


def main():
    print("parse_hdfc_imessages.py — reading HDFC SMS from Messages DB")
    print(f"  DB path : {DB_PATH}")
    print(f"  Window  : last {DAYS_BACK} days")

    # Bypass layer 1 — is the iPhone->Mac SMS sync alive?
    feed = compute_feed_health()
    print(f"  Feed status: {feed['feed_status'].upper()} "
          f"(newest msg {feed.get('last_any_msg_date') or 'n/a'}, "
          f"{feed.get('hours_since_any')}h ago)")

    rows = query_hdfc_messages()
    print(f"  Candidate rows: {len(rows)}")

    transactions = parse_messages(rows)
    print(f"  Parsed SMS transactions: {len(transactions)}")

    # Bypass layer 2 — merge manually-pasted entries (when SMS sync is down)
    manual = load_manual_entries()
    if manual:
        print(f"  Manual bypass entries: {len(manual)}")
    transactions.extend(manual)

    transactions = cross_reference_with_gmail(transactions)

    credits = [t for t in transactions if t['type'] == 'credit']
    debits  = [t for t in transactions if t['type'] == 'debit']
    transfers = [t for t in transactions if t['type'] == 'internal_transfer']
    sms_only_credits = [t for t in credits if t.get('confidence') == 'sms_only']

    manual_count = sum(1 for t in transactions if t.get('source') == 'manual_paste')

    output = {
        'meta': {
            'source': 'imessage_sms',
            'fetched_at': datetime.now().isoformat(),
            'days_back': DAYS_BACK,
            'db_path': str(DB_PATH),
            'raw_candidate_count': len(rows),
            'transaction_count': len(transactions),
            'credit_count': len(credits),
            'debit_count': len(debits),
            'internal_transfer_count': len(transfers),
            'sms_only_count': len(sms_only_credits),
            # --- bypass instrumentation ---
            'feed_status': feed['feed_status'],          # 'live' | 'stale' | 'unknown' (overall phone feed)
            'bank_feed_status': feed.get('bank_feed_status'),            # HDFC bank-sender feed specifically
            'bank_stale_but_phone_live': feed.get('bank_stale_but_phone_live'),  # the false-confidence trap
            'feed_health': feed,
            'manual_entry_count': manual_count,
        },
        'transactions': transactions,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(output, indent=2, ensure_ascii=False, default=str))
    print(f"  Written: {OUTPUT_PATH}")

    # Bypass alert — surface a dead SMS feed loudly so syncs don't give false confidence
    if feed['feed_status'] == 'stale':
        print(f"\n  📵 SMS FEED STALE — newest message in chat.db is "
              f"{feed.get('hours_since_any')}h old (threshold {STALE_THRESHOLD_HOURS}h).")
        print(f"     iPhone->Mac sync is likely DOWN. Bank data is STILL covered by the")
        print(f"     Gmail HDFC email alerts (parse_hdfc_emails.py) — those are server-side.")
        print(f"     To inject a transaction manually, paste the SMS into:")
        print(f"       {MANUAL_PATH}")
    elif feed['feed_status'] == 'unknown':
        print(f"\n  ⚠ SMS feed health unknown ({feed.get('reason', 'no data')}). "
              f"Relying on Gmail HDFC alerts.")

    # Selective-staleness trap: phone feed looks live (promos/OTPs flowing) but no
    # HDFC bank-sender SMS has arrived in a while — the case that produced the false
    # "feed LIVE, no new credit" signal. Surface it loudly so syncs cross-check Gmail.
    if feed.get('bank_stale_but_phone_live'):
        last_bank = feed.get('last_hdfc_sms_date') or 'never'
        h_bank = feed.get('hours_since_hdfc')
        print(f"\n  🏦📵 HDFC BANK-SMS FEED STALE — phone feed is live but the newest HDFC "
              f"bank SMS is {h_bank}h old (last: {last_bank}, threshold {BANK_STALE_THRESHOLD_HOURS}h).")
        print(f"     Likely cause: bank-sender filtering (Filter Unknown Senders) or paused "
              f"iCloud sync (Low Power Mode). Do NOT read this as 'no new credit'.")
        print(f"     CROSS-CHECK against Gmail HDFC alerts; paste any missing SMS into {MANUAL_PATH}.")

    # Actionable summary
    if sms_only_credits:
        print(f"\n  ⚠ {len(sms_only_credits)} SMS-only credit(s) — not yet in Gmail:")
        for t in sms_only_credits:
            amt_str = f"₹{t['amount']:,.0f}"
            cp = t.get('counterparty') or 'unknown'
            src = ' [MANUAL]' if t.get('source') == 'manual_paste' else ''
            print(f"    {t['date'][:16]}  {amt_str}  acc:{t['account']}  from:{cp}{src}")
    else:
        print("  ✅ All SMS credits confirmed in Gmail (or no SMS credits found)")

    # Internal OD<->CA transfers — own money moving between 0247/0241, NOT income/expense.
    if transfers:
        print(f"\n  🔁 {len(transfers)} internal OD↔CA transfer(s) — excluded from credits/debits:")
        for t in transfers:
            amt_str = f"₹{t['amount']:,.0f}"
            print(f"    {t['date'][:16]}  {amt_str}  acc:{t['account']}  (own-account fund transfer)")

    return output


if __name__ == '__main__':
    main()
