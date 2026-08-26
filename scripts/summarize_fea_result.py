#!/usr/bin/env python3
"""Print FEA smoke evidence from result.json. Does not invent values."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT / "simulation" / "workspaces" / "fea-smoke" / "result.json"


def summarize(path: Path) -> int:
    if not path.is_file():
        print(f"ERROR: {path} is missing. The solver did not write a result.", file=sys.stderr)
        return 1
    payload = json.loads(path.read_text(encoding="utf-8"))
    metrics = payload.get("metrics") or {}
    identity = metrics.get("solver_identity") or {}
    termination = metrics.get("termination") or payload.get("termination")
    fields = {
        "solver_status": payload.get("solver_status"),
        "solver_version": identity.get("version"),
        "termination": termination,
        "quality_pass": payload.get("quality_pass"),
        "criterion_verdict": payload.get("criterion_verdict"),
        "work_dir": payload.get("work_dir"),
    }
    for key, value in fields.items():
        print(f"{key}: {value}")
    status = fields["solver_status"]
    if status != "SUCCEEDED":
        print(f"ERROR: solver_status is {status!r}, not SUCCEEDED.", file=sys.stderr)
        return 1
    term_status = termination.get("status") if isinstance(termination, dict) else termination
    if term_status != "NORMAL_TERMINATION":
        print(f"ERROR: termination is {termination!r}, not NORMAL_TERMINATION.", file=sys.stderr)
        return 1
    # INCONCLUSIVE criterion is expected while mill automatic verdict is off.
    # quality_pass is printed as evidence; this script does not fail on it.
    return 0


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT
    return summarize(path)


if __name__ == "__main__":
    raise SystemExit(main())
