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


class StreamGpuBody(BaseModel):
    index: str
    utilization_ratio: float
    memory_used_bytes: int
    memory_total_bytes: int


class StreamSessionCreate(BaseModel):
    role: str
    client: str
    asset_id: str


class StreamHeartbeat(BaseModel):
    gpu: StreamGpuBody | None = None


class WebRtcOffer(BaseModel):
    sdp: str
    type: str
    asset_id: str
    session_id: str | None = None
