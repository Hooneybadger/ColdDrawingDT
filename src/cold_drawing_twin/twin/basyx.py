from __future__ import annotations

import logging
from typing import Any

import httpx

from cold_drawing_twin.config_files import asset_registry

LOGGER = logging.getLogger(__name__)


def shell_id(aas_id: str) -> str:
    return aas_id.replace(":", "_")


def drawing_aas_payload(asset_id: str, state: dict[str, Any]) -> dict[str, Any]:
    registry = asset_registry()
    aas_id = registry[asset_id]["aas_id"]
    return {
        "id": aas_id,
        "idShort": asset_id.replace(".", "_"),
        "modelType": "AssetAdministrationShell",
        "assetInformation": {
            "assetKind": "Instance",
            "globalAssetId": asset_id,
        },
        "submodels": [
            {"type": "ModelReference", "keys": [{"type": "Submodel", "value": f"{aas_id}/ProcessState"}]},
        ],
        "displayName": [{"language": "en", "text": asset_id}],
        "description": [{"language": "en", "text": f"Live Digital Twin for {asset_id}"}],
        "extensions": [
            {"name": "state_version", "value": state.get("state_version")},
            {"name": "usd_prim", "value": registry[asset_id]["usd_prim"]},
        ],
        "processState": state.get("features", {}),
        "evaluationState": {
            "latest_evaluation_id": state.get("latest_evaluation_id"),
            "latest_snapshot_id": state.get("latest_snapshot_id"),
            "verdict": state.get("latest_verdict"),
        },
        "simulationState": {
            "active_fea_job_id": state.get("active_fea_job_id"),
            "last_completed_fea_job_id": state.get("last_completed_fea_job_id"),
        },
    }


class BasyxClient:
    def __init__(self, base_url: str, enabled: bool = True, timeout_s: float = 5.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.enabled = enabled
        self.timeout_s = timeout_s

    def upsert_asset(self, asset_id: str, state: dict[str, Any]) -> None:
        if not self.enabled:
            return
        payload = drawing_aas_payload(asset_id, state)
        url = f"{self.base_url}/shells"
        try:
            with httpx.Client(timeout=self.timeout_s) as client:
                response = client.post(url, json=payload)
                if response.status_code in {409, 400}:
                    client.put(f"{url}/{payload['id']}", json=payload)
        except httpx.HTTPError as exc:
            LOGGER.warning("BaSyx upsert failed for %s: %s", asset_id, exc)
