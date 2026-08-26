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
    assert "automatic_verdict_enabled" in reason
    assert verdict not in {FeaCriterionVerdict.SAFE, FeaCriterionVerdict.UNSAFE}


def test_quality_failure_is_inconclusive():
    verdict, reason = apply_criterion(quality_ok=False, metrics={"peak_von_mises_pa": 1.0})
    assert verdict == FeaCriterionVerdict.INCONCLUSIVE
    assert "quality" in reason


def test_default_mill_config_cannot_yield_safe_even_with_metrics():
    verdict, reason = apply_criterion(
        quality_ok=True,
        metrics={"peak_von_mises_pa": 1.0, "peak_plastic_strain": 0.1},
    )
    assert verdict == FeaCriterionVerdict.INCONCLUSIVE
    assert verdict is not FeaCriterionVerdict.SAFE


def test_enabled_thresholds_can_yield_safe(monkeypatch):
    assert AUTOMATIC_VERDICT_IMPLEMENTED is True
    monkeypatch.setattr(
        "cold_drawing_twin.simulation.postprocess.safety_criterion.fea_criterion",
        lambda: {
            "version": "test-enabled",
            "automatic_verdict_enabled": True,
            "evaluator": "thresholds_v1",
            "policy": {"on_missing_required_metric": "INCONCLUSIVE"},
            "criteria": {"required_thresholds": [{"name": "peak_von_mises_pa", "max": 1e12}]},
        },
    )
    verdict, reason = apply_criterion(quality_ok=True, metrics={"peak_von_mises_pa": 1.0})
    assert verdict == FeaCriterionVerdict.SAFE
    assert "passed" in reason


def test_enabled_thresholds_can_yield_unsafe(monkeypatch):
    monkeypatch.setattr(
        "cold_drawing_twin.simulation.postprocess.safety_criterion.fea_criterion",
        lambda: {
            "version": "test-enabled",
            "automatic_verdict_enabled": True,
            "evaluator": "thresholds_v1",
            "policy": {},
            "criteria": {"required_thresholds": [{"name": "peak_von_mises_pa", "max": 1.0}]},
        },
    )
    verdict, reason = apply_criterion(quality_ok=True, metrics={"peak_von_mises_pa": 10.0})
    assert verdict == FeaCriterionVerdict.UNSAFE
    assert "exceeds" in reason


def test_enabled_empty_thresholds_stay_inconclusive(monkeypatch):
    monkeypatch.setattr(
        "cold_drawing_twin.simulation.postprocess.safety_criterion.fea_criterion",
        lambda: {
            "version": "test-enabled-empty",
            "automatic_verdict_enabled": True,
            "evaluator": "thresholds_v1",
            "policy": {},
            "criteria": {"required_thresholds": []},
        },
    )
    verdict, reason = apply_criterion(quality_ok=True, metrics={"peak_von_mises_pa": 1.0})
    assert verdict == FeaCriterionVerdict.INCONCLUSIVE
    assert "required_thresholds" in reason
