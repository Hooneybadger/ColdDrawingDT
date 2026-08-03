from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum

from asyncua import ua

from cold_drawing_twin.config_files import opcua_map


class OpcQuality(StrEnum):
    GOOD = "GOOD"
    UNCERTAIN = "UNCERTAIN"
    BAD = "BAD"


@dataclass(frozen=True)
class ProcessReading:
    reduction_ratio: float
    die_half_angle_rad: float
    friction_coefficient: float
    normalized_hardening_coefficient: float
    pass_index: int | None
    source_timestamp: datetime | None
    server_timestamp: datetime | None
    quality: str
    source_timestamp_missing: bool
    status_code: str


def nodes_for(asset_id: str) -> dict[str, str]:
    mapping = opcua_map()
    assets = mapping["assets"]
    if asset_id not in assets:
        raise KeyError(asset_id)
    return dict(assets[asset_id])


def quality_from_status(status: ua.StatusCode | None) -> str:
    if status is None:
        return OpcQuality.UNCERTAIN.value
    if status.is_good():
        return OpcQuality.GOOD.value
    if status.is_uncertain():
        return OpcQuality.UNCERTAIN.value
    return OpcQuality.BAD.value


def coerce_timestamp(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
