from __future__ import annotations

from pathlib import Path
from typing import Any


def parse_anim_or_placeholder(work_dir: Path) -> dict[str, Any]:
    summary = work_dir / "fields.json"
    if summary.exists():
        import json

        return json.loads(summary.read_text(encoding="utf-8"))
    return {
        "von_mises_stress": None,
        "equivalent_plastic_strain": None,
        "displacement": None,
        "critical_region": None,
    }
