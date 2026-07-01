from __future__ import annotations

from typing import Any


def damage_metrics(fields: dict[str, Any]) -> dict[str, Any]:
    return {
        "damage_model": None,
        "note": "Damage is a separate postprocess unless a validated OpenRadioss failure model is enabled.",
        "equivalent_plastic_strain": fields.get("equivalent_plastic_strain"),
    }
