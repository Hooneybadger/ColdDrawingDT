from __future__ import annotations

from pydantic import BaseModel, Field


class EvaluationRequest(BaseModel):
    asset_id: str | None = None
    mode: str = "OPERATIONAL"
    expected_state_version: str | None = None


class ScenarioRequest(BaseModel):
    base_snapshot_id: str
    overrides: dict[str, float] = Field(default_factory=dict)


class ProcessStateBody(BaseModel):
    reduction_ratio: float
    die_half_angle_rad: float
    friction_coefficient: float
    normalized_hardening_coefficient: float
    state_version: str | None = None
    quality: str = "GOOD"
