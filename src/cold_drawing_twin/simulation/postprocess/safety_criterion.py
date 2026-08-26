from __future__ import annotations

from typing import Any

from cold_drawing_twin.config_files import fea_criterion
from cold_drawing_twin.domain.types import FeaCriterionVerdict

# Code can compare metrics to versioned thresholds. The mill YAML still leaves
# automatic_verdict_enabled false and required_thresholds empty.
AUTOMATIC_VERDICT_IMPLEMENTED = True
EVALUATOR_NAME = "thresholds_v1"


def quality_pass(histories: dict[str, Any]) -> tuple[bool, str]:
    """Backward-compatible history check used by unit tests."""
    missing = [name for name in ("kinetic_energy", "internal_energy") if not histories.get(name)]
    if missing:
        return False, f"missing histories: {missing}"
    return True, "required histories present"


def _lookup_metric(metrics: dict[str, Any], name: str) -> Any:
    value = metrics.get(name)
    if value is not None and not isinstance(value, dict):
        return value
    fields = metrics.get("fields") or {}
    if name in fields:
        return fields[name]
    histories = metrics.get("histories") or {}
    if name in histories:
        return histories[name]
    return None


def apply_criterion(*, quality_ok: bool, metrics: dict[str, Any]) -> tuple[FeaCriterionVerdict, str]:
    criterion = fea_criterion()
    if not quality_ok:
        return FeaCriterionVerdict.INCONCLUSIVE, "quality failure"
    if not criterion.get("automatic_verdict_enabled", False):
        return (
            FeaCriterionVerdict.INCONCLUSIVE,
            "automatic_verdict_enabled is false; refuse automatic SAFE/UNSAFE",
        )
    evaluator = str(criterion.get("evaluator") or "")
    if evaluator != EVALUATOR_NAME:
        return (
            FeaCriterionVerdict.INCONCLUSIVE,
            f"evaluator {evaluator!r} is not {EVALUATOR_NAME}; refuse automatic SAFE/UNSAFE",
        )
    thresholds = (criterion.get("criteria") or {}).get("required_thresholds") or []
    if not thresholds:
        return (
            FeaCriterionVerdict.INCONCLUSIVE,
            "required_thresholds is empty; refuse automatic SAFE/UNSAFE",
        )
    policy = criterion.get("policy") or {}
    missing_verdict = str(policy.get("on_missing_required_metric") or "INCONCLUSIVE")
    for item in thresholds:
        name = str(item.get("name") or "")
        if not name:
            return FeaCriterionVerdict.INCONCLUSIVE, "threshold is missing a metric name"
        raw = _lookup_metric(metrics, name)
        if raw is None:
            if missing_verdict == "UNSAFE":
                return FeaCriterionVerdict.UNSAFE, f"missing required metric {name}"
            return FeaCriterionVerdict.INCONCLUSIVE, f"missing required metric {name}"
        try:
            value = float(raw)
        except (TypeError, ValueError):
            return FeaCriterionVerdict.INCONCLUSIVE, f"metric {name} is not numeric"
        if "max" in item and value > float(item["max"]):
            return FeaCriterionVerdict.UNSAFE, f"{name} {value} exceeds max {item['max']}"
        if "min" in item and value < float(item["min"]):
            return FeaCriterionVerdict.UNSAFE, f"{name} {value} is below min {item['min']}"
    return FeaCriterionVerdict.SAFE, "all required thresholds passed"
