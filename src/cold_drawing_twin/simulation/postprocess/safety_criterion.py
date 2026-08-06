from __future__ import annotations

from typing import Any

from cold_drawing_twin.config_files import fea_criterion
from cold_drawing_twin.domain.types import FeaCriterionVerdict

# This module has no mill-threshold evaluator. Filling YAML cannot yield SAFE/UNSAFE.
AUTOMATIC_VERDICT_IMPLEMENTED = False


def quality_pass(histories: dict[str, Any]) -> tuple[bool, str]:
    """Backward-compatible history check used by unit tests."""
    missing = [name for name in ("kinetic_energy", "internal_energy") if not histories.get(name)]
    if missing:
        return False, f"missing histories: {missing}"
    return True, "required histories present"


def apply_criterion(*, quality_ok: bool, metrics: dict[str, Any]) -> tuple[FeaCriterionVerdict, str]:
    criterion = fea_criterion()
    if not quality_ok:
        return FeaCriterionVerdict.INCONCLUSIVE, "quality failure"
    parts = ["criterion evaluator is not implemented"]
    if not AUTOMATIC_VERDICT_IMPLEMENTED:
        parts.append("code does not evaluate mill thresholds")
    if not criterion.get("automatic_verdict_enabled", False):
        parts.append("automatic_verdict_enabled is false")
    if str(criterion.get("evaluator") or "unimplemented") == "unimplemented":
        parts.append("evaluator is unimplemented")
    thresholds = (criterion.get("criteria") or {}).get("required_thresholds") or []
    if not thresholds:
        parts.append("required_thresholds is empty")
    return FeaCriterionVerdict.INCONCLUSIVE, "; ".join(parts) + "; refuse automatic SAFE/UNSAFE"
