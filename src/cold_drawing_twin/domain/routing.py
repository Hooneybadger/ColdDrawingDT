from __future__ import annotations

from dataclasses import dataclass

from cold_drawing_twin.domain.types import PinnVerdict, RoutingAction


@dataclass(frozen=True)
class PinnResult:
    verdict: str
    stress_indicator: float | None
    damage_indicator: float | None
    physics_residual: float | None
    confidence: None
    model_version: str
    supported_range: bool
    raw: dict


def route(
    *,
    required_input_missing: bool,
    twin_stale: bool,
    pinn_result: PinnResult | None,
    pinn_invalid: bool,
    site_requires_fea: bool,
) -> RoutingAction:
    """Apply routing-v1 in the documented order. Do not invent extra cutoffs."""
    if required_input_missing:
        return RoutingAction.MANUAL_REVIEW
    if twin_stale:
        return RoutingAction.MANUAL_REVIEW
    if pinn_result is None or pinn_invalid:
        return RoutingAction.MANUAL_REVIEW
    if pinn_result.verdict == PinnVerdict.NEED_FEA:
        return RoutingAction.REQUIRES_FEA
    if site_requires_fea:
        return RoutingAction.REQUIRES_FEA
    if pinn_result.verdict == PinnVerdict.UNSAFE:
        return RoutingAction.REJECT
    if pinn_result.verdict == PinnVerdict.SAFE:
        return RoutingAction.ACCEPT
    return RoutingAction.MANUAL_REVIEW
