import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "summarize_fea_result.py"


def _write(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_summarize_requires_succeeded_solver(tmp_path):
    path = tmp_path / "result.json"
    _write(
        path,
        {
            "solver_status": "SUCCEEDED",
            "quality_pass": True,
            "criterion_verdict": "INCONCLUSIVE",
            "work_dir": str(tmp_path),
            "metrics": {"termination": {"status": "NORMAL_TERMINATION", "normal": True}, "solver_identity": {"version": None}},
        },
    )
    assert subprocess.call([sys.executable, str(SCRIPT), str(path)]) == 0


def test_summarize_fails_when_solver_did_not_run(tmp_path):
    path = tmp_path / "result.json"
    _write(path, {"solver_status": "FAILED", "metrics": {"termination": None}})
    assert subprocess.call([sys.executable, str(SCRIPT), str(path)]) == 1
    assert subprocess.call([sys.executable, str(SCRIPT), str(tmp_path / "missing.json")]) == 1


def test_summarize_accepts_inconclusive_criterion(tmp_path):
    path = tmp_path / "result.json"
    _write(
        path,
        {
            "solver_status": "SUCCEEDED",
            "quality_pass": False,
            "criterion_verdict": "INCONCLUSIVE",
            "work_dir": str(tmp_path),
            "metrics": {"termination": {"status": "NORMAL_TERMINATION", "normal": True}},
        },
    )
    assert subprocess.call([sys.executable, str(SCRIPT), str(path)]) == 0
