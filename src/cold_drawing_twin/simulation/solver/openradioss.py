from __future__ import annotations

import os
import signal
import subprocess
import time
from pathlib import Path


class SolverError(RuntimeError):
    def __init__(self, message: str, status: str = "FAILED") -> None:
        super().__init__(message)
        self.status = status


def run_openradioss(
    *,
    starter_bin: str,
    engine_bin: str,
    starter_file: Path,
    engine_file: Path,
    work_dir: Path,
    timeout_s: int,
) -> dict:
    if not starter_bin or not engine_bin:
        raise SolverError("OPENRADIOSS_STARTER_BIN / OPENRADIOSS_ENGINE_BIN are not set", "FAILED")
    if not Path(starter_bin).exists() or not Path(engine_bin).exists():
        raise SolverError("OpenRadioss binaries were not found", "FAILED")
    _run_checked([starter_bin, "-i", str(starter_file)], work_dir, timeout_s, "Starter")
    _run_checked([engine_bin, "-i", str(engine_file)], work_dir, timeout_s, "Engine")
    return {"status": "SUCCEEDED", "work_dir": str(work_dir)}


def _run_checked(command: list[str], work_dir: Path, timeout_s: int, label: str) -> None:
    start = time.monotonic()
    process = subprocess.Popen(
        command,
        cwd=work_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    try:
        stdout, stderr = process.communicate(timeout=timeout_s)
    except subprocess.TimeoutExpired as exc:
        os.killpg(process.pid, signal.SIGKILL)
        raise SolverError(f"{label} exceeded {timeout_s}s", "TIMEOUT") from exc
    (work_dir / f"{label.lower()}.stdout.log").write_text(stdout, encoding="utf-8")
    (work_dir / f"{label.lower()}.stderr.log").write_text(stderr, encoding="utf-8")
    if process.returncode != 0:
        raise SolverError(f"{label} exited {process.returncode}", "FAILED")
    elapsed = time.monotonic() - start
    (work_dir / f"{label.lower()}.elapsed.txt").write_text(str(elapsed), encoding="utf-8")
