#!/usr/bin/env python3
"""Register a host stream session and heartbeat GPU samples to the API.

Kit still renders on the RTX host. This process only reports liveness and
nvidia-smi numbers. It does not write Decisions.
"""

from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.request

from cold_drawing_twin.observability.gpu import read_nvidia_smi


def _request(url: str, method: str = "GET", payload: dict | None = None) -> dict:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"} if payload is not None else {}
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Report RTX-host stream liveness to the Twin API.")
    parser.add_argument("--api", default="http://127.0.0.1:8000")
    parser.add_argument("--asset-id", default="BG.MIEUM.DRW.04")
    parser.add_argument("--role", default="operator", choices=["operator", "senior"])
    parser.add_argument("--interval", type=float, default=5.0)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args(argv)
    created = _request(
        args.api.rstrip("/") + "/stream/sessions",
        method="POST",
        payload={"role": args.role, "client": "kit", "asset_id": args.asset_id},
    )
    session_id = created["session_id"]
    try:
        while True:
            samples = read_nvidia_smi()
            gpu = None
            if samples:
                sample = samples[0]
                gpu = {
                    "index": sample.index,
                    "utilization_ratio": sample.utilization_ratio,
                    "memory_used_bytes": sample.memory_used_bytes,
                    "memory_total_bytes": sample.memory_total_bytes,
                }
            _request(
                args.api.rstrip("/") + f"/stream/sessions/{session_id}/heartbeat",
                method="POST",
                payload={"gpu": gpu},
            )
            if args.once:
                return 0
            time.sleep(args.interval)
    except (KeyboardInterrupt, urllib.error.URLError):
        try:
            _request(args.api.rstrip("/") + f"/stream/sessions/{session_id}", method="DELETE")
        except urllib.error.URLError:
            pass
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
