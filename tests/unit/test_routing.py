from cold_drawing_twin.domain.features import ProcessFeatures, features_from_mapping, in_supported_range
from cold_drawing_twin.domain.routing import PinnResult, route
from cold_drawing_twin.domain.types import RoutingAction


def test_feature_order_roundtrip():
    features = ProcessFeatures(0.3, 0.2, 0.08, 0.7)
    assert features.as_vector() == [0.3, 0.2, 0.08, 0.7]
    assert features_from_mapping(features.as_dict()).as_vector() == features.as_vector()


def test_range_boundaries():
    assert in_supported_range(ProcessFeatures(0.10, 0.07, 0.03, 0.20))
    assert in_supported_range(ProcessFeatures(0.50, 0.35, 0.15, 1.20))
    assert not in_supported_range(ProcessFeatures(0.09, 0.2, 0.08, 0.7))


def test_confidence_stays_null():
    result = PinnResult("SAFE", 1.0, 0.0, 0.0, None, "v0.1.1", True, {})
    assert result.confidence is None


def test_routing_safe_unsafe_need_fea():
    safe = PinnResult("SAFE", 0, 0, 0, None, "v0.1.1", True, {})
    unsafe = PinnResult("UNSAFE", 0, 0, 0, None, "v0.1.1", True, {})
    need = PinnResult("NEED_FEA", 0, 0, 0, None, "v0.1.1", True, {})
    base = dict(required_input_missing=False, twin_stale=False, pinn_invalid=False, site_requires_fea=False)
    assert route(pinn_result=safe, **base) == RoutingAction.ACCEPT
    assert route(pinn_result=unsafe, **base) == RoutingAction.REJECT
    assert route(pinn_result=need, **base) == RoutingAction.REQUIRES_FEA


def test_routing_stale_and_missing():
    safe = PinnResult("SAFE", 0, 0, 0, None, "v0.1.1", True, {})
    assert (
        route(
            required_input_missing=True,
            twin_stale=False,
            pinn_result=safe,
            pinn_invalid=False,
            site_requires_fea=False,
        )
        == RoutingAction.MANUAL_REVIEW
    )
    assert (
        route(
            required_input_missing=False,
            twin_stale=True,
            pinn_result=safe,
            pinn_invalid=False,
            site_requires_fea=False,
        )
        == RoutingAction.MANUAL_REVIEW
    )
    assert (
        route(
            required_input_missing=False,
            twin_stale=False,
            pinn_result=None,
            pinn_invalid=True,
            site_requires_fea=False,
        )
        == RoutingAction.MANUAL_REVIEW
    )
