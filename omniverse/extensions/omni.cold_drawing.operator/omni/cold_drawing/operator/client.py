from __future__ import annotations

from urllib.request import Request, urlopen
import json

from cold_drawing_twin.display import operator_view


class OperatorClient:
    def __init__(self, base_url: str, asset_id: str = "BG.MIEUM.DRW.04", poll_s: float = 2.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.asset_id = asset_id
        self.poll_s = poll_s

    def fetch_state(self) -> dict:
        with urlopen(self.base_url + f"/assets/{self.asset_id}/state", timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
        payload["asset_id"] = self.asset_id
        return payload

    def status(self) -> dict:
        try:
            return operator_view(self.fetch_state(), backend_online=True)
        except Exception:
            return operator_view({"asset_id": self.asset_id}, backend_online=False)

    def start_stream(self, role: str = "operator", client: str = "kit") -> dict:
        payload = json.dumps({"role": role, "client": client, "asset_id": self.asset_id}).encode("utf-8")
        request = Request(
            self.base_url + "/stream/sessions",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urlopen(request, timeout=5) as response:
            return json.loads(response.read().decode("utf-8"))

    def heartbeat_stream(self, session_id: str, gpu: dict | None = None) -> dict:
        payload = json.dumps({"gpu": gpu}).encode("utf-8")
        request = Request(
            self.base_url + f"/stream/sessions/{session_id}/heartbeat",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urlopen(request, timeout=5) as response:
            return json.loads(response.read().decode("utf-8"))
