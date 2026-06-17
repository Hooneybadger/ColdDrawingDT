from __future__ import annotations

from dataclasses import dataclass

from cold_drawing_twin.config_files import FEATURE_NAMES, FeatureRange, feature_ranges

FEATURE_ORDER = FEATURE_NAMES


class FeatureError(ValueError):
    """Process feature names, order, or range failed a contract check."""


@dataclass(frozen=True)
class ProcessFeatures:
    reduction_ratio: float
    die_half_angle_rad: float
    friction_coefficient: float
    normalized_hardening_coefficient: float

    def as_dict(self) -> dict[str, float]:
        return {
            "reduction_ratio": self.reduction_ratio,
            "die_half_angle_rad": self.die_half_angle_rad,
            "friction_coefficient": self.friction_coefficient,
            "normalized_hardening_coefficient": self.normalized_hardening_coefficient,
        }

    def as_vector(self) -> list[float]:
        return [self.as_dict()[name] for name in FEATURE_ORDER]


def features_from_mapping(data: dict[str, float]) -> ProcessFeatures:
    missing = [name for name in FEATURE_ORDER if name not in data]
    if missing:
        raise FeatureError(f"missing required features: {missing}")
    extra = sorted(set(data) - set(FEATURE_ORDER))
    if extra:
        raise FeatureError(f"unknown features: {extra}")
    values = {name: float(data[name]) for name in FEATURE_ORDER}
    return ProcessFeatures(**values)


def in_supported_range(features: ProcessFeatures, ranges: list[FeatureRange] | None = None) -> bool:
    mapping = features.as_dict()
    for item in ranges or feature_ranges():
        value = mapping[item.name]
        if value < item.minimum or value > item.maximum:
            return False
    return True
