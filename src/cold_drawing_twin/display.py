from __future__ import annotations


VERDICT_DISPLAY = {
    "SAFE": {"text": "Continue the current pass.", "indicator": "green"},
    "UNSAFE": {"text": "Stop. Condition rejected.", "indicator": "red"},
    "INCONCLUSIVE": {"text": "Wait for review.", "indicator": "amber"},
    "MANUAL_REVIEW": {"text": "Wait for review.", "indicator": "amber"},
    "ANALYSIS_REQUIRED": {"text": "Check in progress.", "indicator": "blue"},
}


def operator_view(state: dict) -> dict:
    verdict = state.get("latest_verdict") or "ANALYSIS_REQUIRED"
    display = VERDICT_DISPLAY.get(verdict, VERDICT_DISPLAY["ANALYSIS_REQUIRED"])
    return {
        "asset_id": state.get("asset_id"),
        "process_state": state.get("features") or {},
        "latest_verdict": verdict,
        "fea_running": bool(state.get("active_fea_job_id")),
        "last_update": state.get("source_timestamp") or state.get("ingest_timestamp"),
        "quality": state.get("quality"),
        "text": display["text"],
        "indicator": display["indicator"],
        "display_only": True,
    }


def apply_status_attributes(current: dict, view: dict) -> dict:
    """Return USD custom attribute updates. Does not compute a safety decision."""
    updated = dict(current)
    updated["coldDrawing:verdict"] = view["latest_verdict"]
    updated["coldDrawing:quality"] = view["quality"]
    updated["coldDrawing:feaRunning"] = "true" if view["fea_running"] else "false"
    updated["coldDrawing:lastUpdate"] = view["last_update"]
    updated["coldDrawing:indicator"] = view["indicator"]
    return updated
