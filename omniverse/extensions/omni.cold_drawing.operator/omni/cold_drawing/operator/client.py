from __future__ import annotations

from urllib.request import urlopen
import json


class OperatorClient:
    def __init__(self, base_url: str, asset_id: str = "BG.MIEUM.DRW.04") -> None:
        self.base_url = base_url.rstrip("/")
        self.asset_id = asset_id

    def status(self) -> dict:
        with urlopen(self.base_url + f"/assets/{self.asset_id}/state", timeout=5) as response:
            state = json.loads(response.read().decode("utf-8"))
        verdict = state.get("latest_verdict") or "ANALYSIS_REQUIRED"
        return {
            "asset_id": self.asset_id,
            "verdict": verdict,
            "active_fea_job_id": state.get("active_fea_job_id"),
            "text": _operator_text(verdict),
        }


def _operator_text(verdict: str) -> str:
    mapping = {
        "SAFE": "Continue the current pass.",
        "UNSAFE": "Stop. Condition rejected.",
        "INCONCLUSIVE": "Wait for review.",
        "MANUAL_REVIEW": "Wait for review.",
        "ANALYSIS_REQUIRED": "Check in progress.",
    }
    return mapping.get(verdict, "Check in progress.")
