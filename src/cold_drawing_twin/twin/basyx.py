from __future__ import annotations

import base64
import logging
from datetime import datetime
from typing import Any

import httpx

from cold_drawing_twin.config_files import asset_registry
from cold_drawing_twin.domain.lineage import iso

LOGGER = logging.getLogger(__name__)

PROCESS_ID_SHORT = "ProcessState"
EVALUATION_ID_SHORT = "EvaluationState"
SIMULATION_ID_SHORT = "SimulationState"


def encode_id(identifier: str) -> str:
    """AAS V3 Base64URL encoding without padding."""
    return base64.urlsafe_b64encode(identifier.encode("utf-8")).decode("ascii").rstrip("=")


def submodel_id(aas_id: str, id_short: str) -> str:
    return f"{aas_id}/{id_short}"


def _property(id_short: str, value: Any, value_type: str) -> dict[str, Any]:
    if isinstance(value, datetime):
        rendered = iso(value)
    elif value is None:
        rendered = None
    else:
        rendered = str(value)
    return {
        "modelType": "Property",
        "idShort": id_short,
        "valueType": value_type,
        "value": rendered,
    }


def process_submodel(aas_id: str, state: dict[str, Any]) -> dict[str, Any]:
    features = state.get("features") or {}
    return {
        "modelType": "Submodel",
        "id": submodel_id(aas_id, PROCESS_ID_SHORT),
        "idShort": PROCESS_ID_SHORT,
        "submodelElements": [
            _property("reductionRatio", features.get("reduction_ratio"), "xs:double"),
            _property("dieHalfAngleRad", features.get("die_half_angle_rad"), "xs:double"),
            _property("frictionCoefficient", features.get("friction_coefficient"), "xs:double"),
            _property("normalizedHardeningCoefficient", features.get("normalized_hardening_coefficient"), "xs:double"),
            _property("passIndex", state.get("pass_index"), "xs:int"),
            _property("sourceTimestamp", state.get("source_timestamp"), "xs:dateTime"),
            _property("quality", state.get("quality"), "xs:string"),
            _property("stateVersion", state.get("state_version"), "xs:string"),
        ],
    }


def evaluation_submodel(aas_id: str, state: dict[str, Any]) -> dict[str, Any]:
    return {
        "modelType": "Submodel",
        "id": submodel_id(aas_id, EVALUATION_ID_SHORT),
        "idShort": EVALUATION_ID_SHORT,
        "submodelElements": [
            _property("latestEvaluationId", state.get("latest_evaluation_id"), "xs:string"),
            _property("latestSnapshotId", state.get("latest_snapshot_id"), "xs:string"),
            _property("latestDecisionId", state.get("latest_decision_id"), "xs:string"),
            _property("latestVerdict", state.get("latest_verdict"), "xs:string"),
        ],
    }


def simulation_submodel(aas_id: str, state: dict[str, Any]) -> dict[str, Any]:
    return {
        "modelType": "Submodel",
        "id": submodel_id(aas_id, SIMULATION_ID_SHORT),
        "idShort": SIMULATION_ID_SHORT,
        "submodelElements": [
            _property("activeFeaJobId", state.get("active_fea_job_id"), "xs:string"),
            _property("lastCompletedFeaJobId", state.get("last_completed_fea_job_id"), "xs:string"),
        ],
    }


def drawing_aas_shell(asset_id: str) -> dict[str, Any]:
    registry = asset_registry()
    aas_id = registry[asset_id]["aas_id"]
    refs = [
        {
            "type": "ModelReference",
            "keys": [{"type": "Submodel", "value": submodel_id(aas_id, name)}],
        }
        for name in (PROCESS_ID_SHORT, EVALUATION_ID_SHORT, SIMULATION_ID_SHORT)
    ]
    return {
        "id": aas_id,
        "idShort": asset_id.replace(".", "_"),
        "modelType": "AssetAdministrationShell",
        "assetInformation": {
            "assetKind": "Instance",
            "globalAssetId": asset_id,
        },
        "submodels": refs,
        "displayName": [{"language": "en", "text": asset_id}],
        "description": [{"language": "en", "text": f"Live Digital Twin projection for {asset_id}"}],
    }


class BasyxClient:
    def __init__(self, base_url: str, enabled: bool = True, timeout_s: float = 5.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.enabled = enabled
        self.timeout_s = timeout_s

    def upsert_asset(self, asset_id: str, state: dict[str, Any]) -> None:
        if not self.enabled:
            return
        try:
            self.upsert_shell(asset_id)
            self.upsert_submodels(asset_id, state)
            self.update_submodel_elements(asset_id, state)
        except Exception as exc:  # noqa: BLE001
            LOGGER.warning("BaSyx projection failed for %s: %s", asset_id, exc)

    def upsert_shell(self, asset_id: str) -> None:
        payload = drawing_aas_shell(asset_id)
        self._put_or_post("/shells", payload["id"], payload)

    def upsert_submodels(self, asset_id: str, state: dict[str, Any]) -> None:
        aas_id = asset_registry()[asset_id]["aas_id"]
        for payload in (
            process_submodel(aas_id, state),
            evaluation_submodel(aas_id, state),
            simulation_submodel(aas_id, state),
        ):
            self._put_or_post("/submodels", payload["id"], payload)

    def update_submodel_elements(self, asset_id: str, state: dict[str, Any]) -> None:
        aas_id = asset_registry()[asset_id]["aas_id"]
        for payload in (
            process_submodel(aas_id, state),
            evaluation_submodel(aas_id, state),
            simulation_submodel(aas_id, state),
        ):
            encoded = encode_id(payload["id"])
            for element in payload["submodelElements"]:
                path = f"/submodels/{encoded}/submodel-elements/{element['idShort']}"
                self._request("PUT", path, json=element)

    def get_submodel(self, identifier: str) -> dict[str, Any]:
        response = self._request("GET", f"/submodels/{encode_id(identifier)}")
        return response.json()

    def _put_or_post(self, collection: str, identifier: str, payload: dict[str, Any]) -> None:
        encoded = encode_id(identifier)
        put = self._request("PUT", f"{collection}/{encoded}", json=payload, raise_for_status=False)
        if put.status_code in {200, 201, 204}:
            return
        post = self._request("POST", collection, json=payload, raise_for_status=False)
        if post.status_code not in {200, 201, 204, 409}:
            post.raise_for_status()

    def _request(self, method: str, path: str, json: dict[str, Any] | None = None, raise_for_status: bool = True):
        url = f"{self.base_url}{path}"
        with httpx.Client(timeout=self.timeout_s) as client:
            response = client.request(method, url, json=json)
        if raise_for_status:
            response.raise_for_status()
        return response
