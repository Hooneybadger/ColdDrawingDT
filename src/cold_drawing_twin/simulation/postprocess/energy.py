from __future__ import annotations

import re
from pathlib import Path
from typing import Any


def parse_energy_histories(work_dir: Path) -> dict[str, Any]:
    values: dict[str, list[float]] = {
        "kinetic_energy": [],
        "internal_energy": [],
        "contact_energy": [],
    }
    for path in work_dir.glob("*"):
        if path.suffix.lower() not in {".out", ".txt", ".log", ".t01"}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for name, pattern in (
            ("kinetic_energy", r"KINETIC(?:\s+ENERGY)?\s*[:=]\s*([0-9.Ee+-]+)"),
            ("internal_energy", r"INTERNAL(?:\s+ENERGY)?\s*[:=]\s*([0-9.Ee+-]+)"),
            ("contact_energy", r"CONTACT(?:\s+ENERGY)?\s*[:=]\s*([0-9.Ee+-]+)"),
        ):
            for match in re.finditer(pattern, text, re.I):
                values[name].append(float(match.group(1)))
    return values
