"""First Rain daily pipeline orchestrator.

Runs each deterministic stage as an isolated subprocess. Snapshots the prior
good output before running and restores it on failure, so a single broken stage
never leaves a half-built artifact. Always writes pipeline_health.json and exits 0
in --best-effort mode (the health report, not the exit code, carries status).
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pipeline_health as ph

VAULT_ROOT = Path(__file__).resolve().parents[2]
PY = sys.executable
STAGE_TIMEOUT = 300  # seconds per stage


class Stage:
    def __init__(self, name, script, output, source, args=None, snapshot=True,
                 input_path=None, input_max_age=24.0, input_required_keys=()):
        self.name = name
        self.script = script
        self.output = output
        self.source = source
        self.args = list(args or [])
        self.snapshot = snapshot
        self.input_path = input_path
        self.input_max_age = input_max_age
        self.input_required_keys = tuple(input_required_keys)


def _last_line(text):
    lines = (text or "").strip().splitlines()
    return lines[-1] if lines else ""


def run_stage(stage, root=VAULT_ROOT, timeout=STAGE_TIMEOUT):
    """Run one stage. Returns (ok: bool, detail: str). Never raises."""
    root = Path(root)
    out_path = root / stage.output
    lg_dir = root / "data" / "projects" / "last_good"
    if stage.snapshot:
        ph.snapshot_last_good(out_path, lg_dir)
    cmd = [PY, str(root / "scripts" / "projects" / stage.script)] + stage.args
    try:
        proc = subprocess.run(cmd, cwd=str(root), capture_output=True,
                              text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        restored = ph.restore_last_good(out_path, lg_dir)
        return False, f"timeout after {timeout}s (restored={restored})"
    except Exception as exc:  # pragma: no cover - defensive
        restored = ph.restore_last_good(out_path, lg_dir)
        return False, f"launch error: {exc} (restored={restored})"
    if proc.returncode != 0:
        restored = ph.restore_last_good(out_path, lg_dir)
        return False, f"exit {proc.returncode}: {_last_line(proc.stderr or proc.stdout)} (restored={restored})"
    return True, _last_line(proc.stdout) or "ok"


def _input_status(stage, root, now):
    """Freshness of the stage's declared raw input (if any). 'fresh' when no input declared."""
    if not stage.input_path:
        return "fresh"
    path = Path(root) / stage.input_path
    if stage.input_required_keys:
        validator = lambda p: ph.is_valid_json(p, required_keys=stage.input_required_keys)
    else:
        validator = ph.is_nonempty
    return ph.freshness(path, stage.input_max_age, now=now, validator=validator)


def run_pipeline(stages, root=VAULT_ROOT, now=None):
    """Run all stages, never abort, write pipeline_health.json, return the report."""
    root = Path(root)
    report = ph.new_report(now=now)
    for stage in stages:
        in_status = _input_status(stage, root, now)
        ok, detail = run_stage(stage, root=root)
        out_path = root / stage.output
        if ok:
            stage_status = "fresh"
        elif ph.is_nonempty(out_path):
            stage_status = "stale"   # failed but last-good restored a usable artifact
        else:
            stage_status = "failed"
        status = ph.worst(in_status, stage_status)
        age = ph.file_age_hours(out_path, now=now)
        if in_status != "fresh" and stage_status == "fresh":
            detail = f"input {in_status}; {detail}".strip()
        ph.set_source(report, stage.source, status, age_hours=age, detail=detail)
    ph.finalize(report)
    ph.write_health(report, root / "data" / "projects" / "pipeline_health.json")
    return report


if __name__ == "__main__":  # pragma: no cover - wired in Task 6
    raise SystemExit("run_pipeline orchestration entrypoint added in Task 6")
