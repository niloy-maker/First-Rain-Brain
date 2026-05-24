"""Health + freshness helpers for the First Rain daily pipeline.
Pure stdlib. No side effects on import. Safe to call from run_pipeline or tests.
"""
from __future__ import annotations

import json
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path

VAULT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = VAULT_ROOT / "data" / "projects"
LAST_GOOD_DIR = DATA_DIR / "last_good"
HEALTH_PATH = DATA_DIR / "pipeline_health.json"

_SEVERITY = {"fresh": 0, "stale": 1, "failed": 2}


def is_nonempty(path) -> bool:
    p = Path(path)
    return p.exists() and p.is_file() and p.stat().st_size > 0


def is_valid_json(path, required_keys=()) -> bool:
    p = Path(path)
    if not is_nonempty(p):
        return False
    try:
        data = json.loads(p.read_text())
    except (ValueError, OSError):
        return False
    if isinstance(data, dict):
        return all(k in data for k in required_keys)
    return not required_keys


def file_age_hours(path, now=None):
    p = Path(path)
    if not p.exists():
        return None
    now = time.time() if now is None else now
    return (now - p.stat().st_mtime) / 3600.0


def freshness(path, max_age_hours, now=None, validator=None) -> str:
    """Return 'fresh' | 'stale' | 'failed'.
    validator: callable(path)->bool deciding usability. Defaults to is_nonempty.
    Boundary is exclusive: a file aged exactly max_age_hours is still 'fresh';
    it becomes 'stale' only once age strictly exceeds the threshold.
    """
    validator = validator or is_nonempty
    if not validator(path):
        return "failed"
    age = file_age_hours(path, now=now)
    if age is None:
        return "failed"
    return "stale" if age > max_age_hours else "fresh"  # exclusive: age == max_age_hours → "fresh"


def worst(*statuses) -> str:
    """Return the most severe status among the args (failed > stale > fresh).
    Empty input returns 'fresh'.
    """
    if not statuses:
        return "fresh"
    return max(statuses, key=lambda s: _SEVERITY[s])


def snapshot_last_good(path, last_good_dir=LAST_GOOD_DIR, validator=None) -> bool:
    """Copy path -> last_good_dir/<name> ONLY if it passes validator.
    Prevents poisoning last_good with an empty/corrupt artifact. Returns True if copied.
    """
    validator = validator or is_nonempty
    p = Path(path)
    if not validator(p):
        return False
    lg = Path(last_good_dir)
    lg.mkdir(parents=True, exist_ok=True)
    shutil.copy2(p, lg / p.name)
    return True


def restore_last_good(path, last_good_dir=LAST_GOOD_DIR) -> bool:
    """Copy last_good_dir/<name> -> path if a snapshot exists. Returns True if restored."""
    p = Path(path)
    src = Path(last_good_dir) / p.name
    if not src.exists():
        return False
    p.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, p)
    return True
