from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import yaml

from cold_drawing_twin.paths import CONFIG_DIR

FEATURE_NAMES = (
    "reduction_ratio",
    "die_half_angle_rad",
    "friction_coefficient",
    "normalized_hardening_coefficient",
)


def load_yaml(name: str) -> dict[str, Any]:
    path = CONFIG_DIR / name
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{name} must be a mapping")
    return data


def pinn_contract() -> dict[str, Any]:
    return load_yaml("pinn_contract.yaml")


def routing_policy() -> dict[str, Any]:
    return load_yaml("routing_policy.yaml")


def freshness_policy() -> dict[str, Any]:
    return load_yaml("freshness.yaml")


def site_policy() -> dict[str, Any]:
    return load_yaml("site_policy.yaml")


def asset_registry() -> dict[str, Any]:
    return load_yaml("asset_registry.yaml")["assets"]


def factory_layout() -> dict[str, Any]:
    return load_yaml("factory_layout.yaml")


def fea_reference() -> dict[str, Any]:
    return load_yaml("fea_reference_case.yaml")


def fea_criterion() -> dict[str, Any]:
    return load_yaml("fea_safety_criterion.yaml")


def fea_quality() -> dict[str, Any]:
    return load_yaml("fea_quality.yaml")


def hardening_map() -> dict[str, Any]:
    return load_yaml("hardening_map.yaml")


def opcua_map() -> dict[str, Any]:
    return load_yaml("opcua_map.yaml")


@dataclass(frozen=True)
class FeatureRange:
    name: str
    minimum: float
    maximum: float


def feature_ranges() -> list[FeatureRange]:
    return [
        FeatureRange(item["name"], float(item["min"]), float(item["max"]))
        for item in pinn_contract()["features"]
    ]
