from __future__ import annotations

from pathlib import Path
from typing import Any

from cold_drawing_twin.simulation.postprocess.parser import parse_energy_listing, parse_solver_outputs


def parse_energy_histories(work_dir: Path) -> dict[str, Any]:
    parsed = parse_solver_outputs(work_dir)
    histories = parsed["histories"]
    if any(histories.values()):
        return histories
    text = ""
    for path in work_dir.glob("*"):
        if path.suffix.lower() in {".out", ".txt", ".log"}:
            text += path.read_text(encoding="utf-8", errors="replace")
    return parse_energy_listing(text)
