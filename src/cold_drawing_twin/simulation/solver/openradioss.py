from __future__ import annotations

import os
import re
import signal
import subprocess
import time
from pathlib import Path

from cold_drawing_twin.domain.timeouts import FEA_CONVERSION_TOOL_TIMEOUT_S


class SolverError(RuntimeError):
    def __init__(self, message: str, status: str = "FAILED") -> None:
        super().__init__(message)
        self.status = status


def solver_environment(starter_bin: str) -> dict[str, str]:
    env = os.environ.copy()
    starter = Path(starter_bin).resolve()
    root = starter.parent.parent if starter.parent.name == "exec" else starter.parent
    env["OPENRADIOSS_PATH"] = str(root)
    cfg = root / "hm_cfg_files"
    if cfg.exists():
        env["RAD_CFG_PATH"] = str(cfg)
    h3d = root / "extlib" / "h3d" / "lib" / "linux64"
    hm = root / "extlib" / "hm_reader" / "linux64"
    extra = [str(path) for path in (h3d, hm) if path.exists()]
    if extra:
        env["LD_LIBRARY_PATH"] = os.pathsep.join(extra + [env.get("LD_LIBRARY_PATH", "")])
    env.setdefault("OMP_STACKSIZE", "400m")
    env.setdefault("OMP_NUM_THREADS", "1")
    return env


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
    env = solver_environment(starter_bin)
    _run_checked([starter_bin, "-i", str(starter_file.name), "-np", "1"], work_dir, timeout_s, "starter", env)
    _run_checked([engine_bin, "-i", str(engine_file.name)], work_dir, timeout_s, "engine", env)
    _convert_outputs(engine_bin, work_dir, env)
    return {"status": "SUCCEEDED", "work_dir": str(work_dir)}


def _convert_outputs(engine_bin: str, work_dir: Path, env: dict[str, str]) -> None:
    parent = Path(engine_bin).resolve().parent
    th_tool = _find_tool(parent, "th_to_csv")
    if th_tool is not None:
        for t01 in work_dir.glob("*T01"):
            subprocess.run(
                [str(th_tool), t01.name],
                cwd=work_dir,
                env=env,
                check=False,
                capture_output=True,
                text=True,
                timeout=FEA_CONVERSION_TOOL_TIMEOUT_S,
            )
    anim_tool = _find_tool(parent, "anim_to_vtk")
    if anim_tool is None:
        return
    for frame in sorted(path for path in work_dir.iterdir() if re.fullmatch(r".*A\d{3}", path.name)):
        vtk_path = work_dir / f"{frame.name}.vtk"
        completed = subprocess.run(
            [str(anim_tool), frame.name],
            cwd=work_dir,
            env=env,
            check=False,
            capture_output=True,
            text=True,
            timeout=FEA_CONVERSION_TOOL_TIMEOUT_S,
        )
        stdout = completed.stdout or ""
        if stdout.lstrip().startswith("# vtk"):
            vtk_path.write_text(stdout, encoding="utf-8")


def _find_tool(directory: Path, prefix: str) -> Path | None:
    matches = sorted(path for path in directory.iterdir() if path.is_file() and path.name.startswith(prefix))
    return matches[0] if matches else None


def _run_checked(command: list[str], work_dir: Path, timeout_s: int, label: str, env: dict[str, str]) -> None:
    start = time.monotonic()
    process = subprocess.Popen(
        command,
        cwd=work_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
        env=env,
    )
    try:
        stdout, stderr = process.communicate(timeout=timeout_s)
    except subprocess.TimeoutExpired as exc:
        os.killpg(process.pid, signal.SIGKILL)
        raise SolverError(f"{label} exceeded {timeout_s}s", "TIMEOUT") from exc
    (work_dir / f"{label}.stdout.log").write_text(stdout, encoding="utf-8")
    (work_dir / f"{label}.stderr.log").write_text(stderr, encoding="utf-8")
    if process.returncode != 0:
        raise SolverError(f"{label} exited {process.returncode}", "FAILED")
    elapsed = time.monotonic() - start
    (work_dir / f"{label}.elapsed.txt").write_text(str(elapsed), encoding="utf-8")
