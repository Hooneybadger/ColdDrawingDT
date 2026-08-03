from __future__ import annotations

from typing import Any

from cold_drawing_twin.config_files import fea_criterion
from cold_drawing_twin.domain.types import FeaCriterionVerdict


def quality_pass(histories: dict[str, Any]) -> tuple[bool, str]:
    """Backward-compatible history check used by unit tests."""
    missing = [name for name in ("kinetic_energy", "internal_energy") if not histories.get(name)]
    if missing:
        return False, f"missing histories: {missing}"
    return True, "required histories present"


def apply_criterion(*, quality_ok: bool, metrics: dict[str, Any]) -> tuple[FeaCriterionVerdict, str]:
    criterion = fea_criterion()
    _policy = criterion["policy"]
    thresholds = criterion["criteria"].get("required_thresholds") or []
    if not quality_ok:
        return FeaCriterionVerdict.INCONCLUSIVE, "quality failure"
    if not thresholds:
        return FeaCriterionVerdict.INCONCLUSIVE, "required_thresholds is empty; refuse automatic SAFE/UNSAFE"
    return FeaCriterionVerdict.INCONCLUSIVE, "no automatic FEA verdict in this criterion version"
