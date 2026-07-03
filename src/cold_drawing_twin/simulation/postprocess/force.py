from __future__ import annotations

import re
from pathlib import Path
from typing import Any


def parse_drawing_force(work_dir: Path) -> dict[str, Any]:
    samples: list[float] = []
    for path in work_dir.glob("*"):
        if path.suffix.lower() not in {".out", ".txt", ".log"}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for match in re.finditer(r"(?:DRAWING|REACTION)\s+FORCE\s*[:=]\s*([0-9.Ee+-]+)", text, re.I):
            samples.append(float(match.group(1)))
    return {"drawing_force": samples}
