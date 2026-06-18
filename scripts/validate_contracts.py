#!/usr/bin/env python3
"""Check that this version's config, schemas, and examples still agree."""

from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("install pyyaml before running this script") from exc

try:
    from jsonschema import Draft202012Validator
    from jsonschema.exceptions import SchemaError
except ImportError as exc:  # pragma: no cover
    raise SystemExit("install jsonschema before running this script") from exc

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config"
SCHEMAS = ROOT / "schemas"
EXAMPLES = ROOT / "docs" / "examples"

FEATURE_NAMES = [
    "reduction_ratio",
    "die_half_angle_rad",
    "friction_coefficient",
    "normalized_hardening_coefficient",
]


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def load_yaml(path: Path) -> object:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        fail(f"{path.relative_to(ROOT)} is not valid YAML: {exc}")
    if data is None:
        fail(f"{path.relative_to(ROOT)} is empty")
    return data


def load_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"{path.relative_to(ROOT)} is not valid JSON: {exc}")


def check_feature_order(pinn: dict, snapshot_schema: dict) -> None:
    names = [item["name"] for item in pinn["features"]]
    if names != FEATURE_NAMES:
        fail(f"PINN feature names {names} do not match {FEATURE_NAMES}")
    required = snapshot_schema["properties"]["features"]["required"]
    if required != FEATURE_NAMES:
        fail(f"snapshot schema feature order {required} does not match {FEATURE_NAMES}")


def check_assets(layout: dict, registry: dict) -> None:
    layout_ids = [item["id"] for item in layout["assets"]]
    layout_ids.extend(item["id"] for item in layout["cranes"])
    registry_ids = list(registry["assets"].keys())
    if sorted(layout_ids) != sorted(registry_ids):
        missing = sorted(set(layout_ids) - set(registry_ids))
        extra = sorted(set(registry_ids) - set(layout_ids))
        fail(f"asset IDs differ. missing_from_registry={missing} extra_in_registry={extra}")
    if len(layout_ids) != len(set(layout_ids)):
        fail("factory layout has duplicate asset IDs")
    if "BG.MIEUM.DRW.04" not in layout_ids:
        fail("Drawing 4 asset ID BG.MIEUM.DRW.04 is missing")
    drawing = next(item for item in layout["assets"] if item["id"] == "BG.MIEUM.DRW.04")
    expected = {"x": 18.0, "y": 7.4, "l": 35.5, "w": 5.5, "h": 2.8}
    for key, value in expected.items():
        if float(drawing[key]) != value:
            fail(f"Drawing 4 {key} is {drawing[key]}, expected {value}")


def check_examples(snapshot_schema: dict, decision_schema: dict) -> None:
    Draft202012Validator.check_schema(snapshot_schema)
    Draft202012Validator.check_schema(decision_schema)
    snapshot_validator = Draft202012Validator(snapshot_schema)
    decision_validator = Draft202012Validator(decision_schema)

    snapshot = load_json(EXAMPLES / "process_snapshot.example.json")
    errors = sorted(snapshot_validator.iter_errors(snapshot), key=lambda item: item.path)
    if errors:
        fail(f"process_snapshot.example.json failed schema: {errors[0].message}")

    for name in ("decision.example.json", "decision_fea.example.json"):
        decision = load_json(EXAMPLES / name)
        errors = sorted(decision_validator.iter_errors(decision), key=lambda item: item.path)
        if errors:
            fail(f"{name} failed schema: {errors[0].message}")

    prediction = load_json(EXAMPLES / "prediction_result.example.json")
    if prediction.get("confidence") is not None:
        fail("prediction example must keep confidence as null when unused")
    if prediction.get("verdict") != "NEED_FEA":
        fail("prediction example should show the NEED_FEA path")


def main() -> None:
    required_yaml = [
        "asset_registry.yaml",
        "factory_layout.yaml",
        "fea_reference_case.yaml",
        "fea_safety_criterion.yaml",
        "pinn_contract.yaml",
        "routing_policy.yaml",
    ]
    for name in required_yaml:
        path = CONFIG / name
        if not path.exists():
            fail(f"missing {path.relative_to(ROOT)}")

    pinn = load_yaml(CONFIG / "pinn_contract.yaml")
    routing = load_yaml(CONFIG / "routing_policy.yaml")
    layout = load_yaml(CONFIG / "factory_layout.yaml")
    registry = load_yaml(CONFIG / "asset_registry.yaml")
    fea_ref = load_yaml(CONFIG / "fea_reference_case.yaml")
    fea_crit = load_yaml(CONFIG / "fea_safety_criterion.yaml")
    snapshot_schema = load_json(SCHEMAS / "process_snapshot.schema.json")
    decision_schema = load_json(SCHEMAS / "decision.schema.json")

    if pinn["model"]["release"] != "v0.1.1":
        fail("PINN release in config is not v0.1.1")
    if routing.get("version") != "routing-v1":
        fail("routing policy version is not routing-v1")
    if fea_ref.get("version") != "fea-reference-v1":
        fail("FEA reference version is not fea-reference-v1")
    if fea_crit.get("version") != "fea-criterion-v1":
        fail("FEA criterion version is not fea-criterion-v1")
    if fea_crit["criteria"].get("required_thresholds") != []:
        fail("this version still has empty FEA thresholds; do not pretend they are filled")

    try:
        Draft202012Validator.check_schema(snapshot_schema)
        Draft202012Validator.check_schema(decision_schema)
    except SchemaError as exc:
        fail(f"schema is invalid: {exc}")

    check_feature_order(pinn, snapshot_schema)
    check_assets(layout, registry)
    check_examples(snapshot_schema, decision_schema)

    svg = ROOT / "docs" / "images" / "factory-layout.svg"
    if not svg.exists():
        fail("docs/images/factory-layout.svg is missing")
    svg_text = svg.read_text(encoding="utf-8")
    if "DRW.04" not in svg_text:
        fail("docs/images/factory-layout.svg is missing Drawing 4")

    print("contracts ok")
    print(f"assets: {len(registry['assets'])}")
    print(f"PINN: {pinn['model']['release']}")
    print(f"routing: {routing['version']}")


if __name__ == "__main__":
    main()
