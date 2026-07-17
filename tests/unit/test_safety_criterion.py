from cold_drawing_twin.simulation.postprocess.safety_criterion import apply_criterion, quality_pass
from cold_drawing_twin.domain.types import FeaCriterionVerdict


def test_quality_fail_without_histories():
    ok, reason = quality_pass({"kinetic_energy": [], "internal_energy": [], "drawing_force": []})
    assert not ok
    assert "missing" in reason


def test_empty_thresholds_refuse_automatic_verdict():
    verdict, reason = apply_criterion(quality_ok=True, metrics={})
    assert verdict == FeaCriterionVerdict.INCONCLUSIVE
    assert "required_thresholds" in reason
