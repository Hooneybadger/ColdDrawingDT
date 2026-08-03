from __future__ import annotations

from pathlib import Path
from typing import Any

from cold_drawing_twin.simulation.postprocess.parser import parse_solver_outputs


def parse_drawing_force(work_dir: Path) -> dict[str, Any]:
    parsed = parse_solver_outputs(work_dir)
    return {"drawing_force": parsed["histories"].get("drawing_force") or []}
