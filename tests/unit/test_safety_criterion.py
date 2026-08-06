from cold_drawing_twin.simulation.postprocess.safety_criterion import (
    AUTOMATIC_VERDICT_IMPLEMENTED,
    apply_criterion,
    quality_pass,
)
from cold_drawing_twin.domain.types import FeaCriterionVerdict


def test_quality_fail_without_histories():
    ok, reason = quality_pass({"kinetic_energy": [], "internal_energy": [], "drawing_force": []})
    assert not ok
    assert "missing" in reason


def test_empty_thresholds_refuse_automatic_verdict():
    verdict, reason = apply_criterion(quality_ok=True, metrics={})
    assert verdict == FeaCriterionVerdict.INCONCLUSIVE
    assert "required_thresholds" in reason
    assert "not implemented" in reason


def test_quality_failure_is_inconclusive():
    verdict, reason = apply_criterion(quality_ok=False, metrics={"peak_von_mises_pa": 1.0})
    assert verdict == FeaCriterionVerdict.INCONCLUSIVE
    assert "quality" in reason


def test_placeholder_thresholds_cannot_yield_safe(monkeypatch):
    monkeypatch.setattr(
        "cold_drawing_twin.simulation.postprocess.safety_criterion.fea_criterion",
        lambda: {
            "version": "test-filled",
            "automatic_verdict_enabled": True,
            "evaluator": "thresholds_v1",
            "policy": {},
            "criteria": {"required_thresholds": [{"name": "peak_von_mises_pa", "max": 1e12}]},
        },
    )
    verdict, reason = apply_criterion(quality_ok=True, metrics={"peak_von_mises_pa": 1.0})
    assert verdict == FeaCriterionVerdict.INCONCLUSIVE
    assert verdict not in {FeaCriterionVerdict.SAFE, FeaCriterionVerdict.UNSAFE}
    assert "not implemented" in reason
    assert AUTOMATIC_VERDICT_IMPLEMENTED is False
