from __future__ import annotations

from urllib.request import urlopen
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
        return operator_view(self.fetch_state())
