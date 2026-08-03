from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from typing import Any


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def idempotency_hash(
    snapshot_id: str,
    fea_profile_version: str,
    material_mapping_version: str,
    mesh_config_version: str,
    solver_version: str,
    safety_criterion_version: str,
) -> str:
    payload = "|".join(
        [
            snapshot_id,
            fea_profile_version,
            material_mapping_version,
            mesh_config_version,
            solver_version,
            safety_criterion_version,
        ]
    )
    return sha256(payload.encode("utf-8")).hexdigest()


def lineage_record(
    *,
    asset_id: str,
    state_version: str | None,
    source_timestamp: datetime | str | None,
    snapshot: dict[str, Any],
    pinn: dict[str, Any] | None,
    pinn_input: dict[str, Any] | None,
    routing_policy_version: str,
    routing_action: str,
    fea: dict[str, Any] | None = None,
    decision: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "asset_id": asset_id,
        "state_version": state_version,
        "source_timestamp": source_timestamp if isinstance(source_timestamp, str) else iso(source_timestamp),
        "snapshot_id": snapshot.get("snapshot_id"),
        "snapshot": snapshot,
        "pinn": {
            "model_version": None if pinn is None else pinn.get("model_version"),
            "input": pinn_input,
            "output": pinn,
        },
        "routing": {
            "policy_version": routing_policy_version,
            "action": routing_action,
        },
        "fea": fea,
        "decision": decision,
    }
