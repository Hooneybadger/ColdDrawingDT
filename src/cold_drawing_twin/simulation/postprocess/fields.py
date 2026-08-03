from __future__ import annotations

from pathlib import Path
from typing import Any


def placeholder_fields() -> dict[str, Any]:
    """Explicit empty field set. Not a solver result."""
    return {
        "von_mises_stress": None,
        "equivalent_plastic_strain": None,
        "displacement": None,
        "critical_region": None,
        "placeholder": True,
    }


def parse_anim_or_placeholder(work_dir: Path) -> dict[str, Any]:
    summary = work_dir / "fields.json"
    if summary.exists():
        import json

        payload = json.loads(summary.read_text(encoding="utf-8"))
        payload["placeholder"] = False
        payload["source"] = "fields.json"
        return payload
    return placeholder_fields()
