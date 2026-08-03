from __future__ import annotations

import json
from urllib.request import Request, urlopen


class TwinApiClient:
    """Kit extensions call the HTTP API. They never open the database."""

    def __init__(self, base_url: str, poll_s: float = 2.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.poll_s = poll_s

    def get_json(self, path: str) -> dict:
        with urlopen(self.base_url + path, timeout=5) as response:
            return json.loads(response.read().decode("utf-8"))

    def post_json(self, path: str, payload: dict) -> dict:
        data = json.dumps(payload).encode("utf-8")
        request = Request(self.base_url + path, data=data, headers={"Content-Type": "application/json"})
        with urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))

    def assets(self) -> dict:
        return self.get_json("/assets")

    def asset_state(self, asset_id: str) -> dict:
        return self.get_json(f"/assets/{asset_id}/state")

    def history(self, asset_id: str) -> dict:
        return self.get_json(f"/assets/{asset_id}/history")

    def evaluate(self, asset_id: str, expected_state_version: str | None = None) -> dict:
        body = {"mode": "OPERATIONAL"}
        if expected_state_version:
            body["expected_state_version"] = expected_state_version
        return self.post_json(f"/assets/{asset_id}/evaluations", body)

    def decision(self, decision_id: str) -> dict:
        return self.get_json(f"/decisions/{decision_id}")

    def fea_job(self, job_id: str) -> dict:
        return self.get_json(f"/fea-jobs/{job_id}")
