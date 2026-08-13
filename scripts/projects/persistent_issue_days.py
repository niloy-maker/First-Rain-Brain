#!/usr/bin/env python3
"""Count how many consecutive days an issue string has appeared in the
morning briefings — for the Telegram redesign's "🚨 PERSISTENT (day N)" line.

Reads back through `_outputs/briefing-YYYY-MM-DD.md` files from today going
backwards. Consecutive-day count breaks the moment a briefing exists but
doesn't contain the substring (or a briefing is missing).

Also used by the heal-check to suppress items already flagged in today's
briefing — see the `already_in_today` helper.

Usage:
    persistent_issue_days.py days "Notion connector" [--max-days 30]
      -> prints an integer (0 if never seen or not in today's briefing)

    persistent_issue_days.py already-in-today "Notion connector"
      -> exits 0 if the substring is in today's briefing, 1 otherwise
      (case-insensitive substring match)
"""
from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path

BRIEFINGS_DIR = Path("_outputs")
DEFAULT_MAX_DAYS = 30


def _briefing_path(d: date) -> Path:
    return BRIEFINGS_DIR / f"briefing-{d.isoformat()}.md"


def consecutive_days(substring: str, max_days: int = DEFAULT_MAX_DAYS) -> int:
    """Number of consecutive days (including today) where the substring
    appears in the briefing file. Case-insensitive. Returns 0 if today's
    briefing doesn't contain it (i.e. the streak has broken today)."""
    needle = substring.lower()
    days = 0
    today = date.today()
    for i in range(max_days):
        d = today - timedelta(days=i)
        p = _briefing_path(d)
        if not p.exists():
            # No briefing for this day — streak breaks
            return days
        try:
            content = p.read_text().lower()
        except OSError:
            return days
        if needle in content:
            days += 1
        else:
            return days
    return days


def already_in_today(substring: str) -> bool:
    p = _briefing_path(date.today())
    if not p.exists():
        return False
    try:
        return substring.lower() in p.read_text().lower()
    except OSError:
        return False


def _cli(argv: list[str]) -> int:
    if len(argv) < 3:
        print(__doc__, file=sys.stderr)
        return 2
    cmd, needle = argv[1], argv[2]
    if cmd == "days":
        max_days = DEFAULT_MAX_DAYS
        if "--max-days" in argv:
            try:
                max_days = int(argv[argv.index("--max-days") + 1])
            except (ValueError, IndexError):
                print("bad --max-days value", file=sys.stderr)
                return 2
        print(consecutive_days(needle, max_days))
        return 0
    if cmd == "already-in-today":
        return 0 if already_in_today(needle) else 1
    print(f"unknown command: {cmd}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(_cli(sys.argv))
