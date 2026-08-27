from __future__ import annotations

from typing import Any

UNAVAILABLE = "—"
NEUTRAL_INDICATOR = "gray"
NEUTRAL_COLOR = (0.45, 0.45, 0.45)

VERDICT_DISPLAY = {
    "SAFE": {
        "text": "Continue the current pass.",
        "indicator": "green",
        "color": (0.18, 0.55, 0.22),
    },
    "UNSAFE": {
        "text": "Stop. Condition rejected.",
        "indicator": "red",
        "color": (0.75, 0.12, 0.12),
    },
    "INCONCLUSIVE": {
        "text": "Wait for review.",
        "indicator": "amber",
        "color": (0.85, 0.60, 0.10),
    },
    "MANUAL_REVIEW": {
        "text": "Wait for review.",
        "indicator": "amber",
        "color": (0.85, 0.60, 0.10),
    },
    "ANALYSIS_REQUIRED": {
        "text": "Check in progress.",
        "indicator": "blue",
        "color": (0.12, 0.40, 0.75),
    },
}


def dash(value: Any) -> str:
    if value is None or value == "":
        return UNAVAILABLE
    return str(value)


def verdict_style(verdict: str | None, *, backend_online: bool = True) -> dict[str, Any]:
    """Map a backend verdict to display color. Transport failure is not a verdict."""
    if not backend_online:
        return {
            "verdict": None,
            "text": "Backend OFFLINE. State unavailable.",
            "indicator": NEUTRAL_INDICATOR,
            "color": NEUTRAL_COLOR,
        }
    if not verdict:
        return {
            "verdict": None,
            "text": "No Decision yet.",
            "indicator": NEUTRAL_INDICATOR,
            "color": NEUTRAL_COLOR,
        }
    style = VERDICT_DISPLAY.get(verdict)
    if style is None:
        return {
            "verdict": verdict,
            "text": "Unknown verdict.",
            "indicator": NEUTRAL_INDICATOR,
            "color": NEUTRAL_COLOR,
        }
    return {"verdict": verdict, **style}


def operator_view(state: dict | None, *, backend_online: bool = True) -> dict:
    """Display-only operator payload. Does not invent an engineering verdict."""
    payload = state or {}
    style = verdict_style(payload.get("latest_verdict"), backend_online=backend_online)
    return {
        "asset_id": payload.get("asset_id"),
        "process_state": payload.get("features") or {},
        "latest_verdict": style["verdict"],
        "evaluation_id": payload.get("latest_evaluation_id") or payload.get("evaluation_id"),
        "snapshot_id": payload.get("latest_snapshot_id") or payload.get("snapshot_id"),
        "decision_id": payload.get("latest_decision_id") or payload.get("decision_id"),
        "routing_action": payload.get("routing_action"),
        "model_version": payload.get("model_version"),
        "fea_job_id": payload.get("active_fea_job_id") or payload.get("fea_job_id"),
        "fea_running": bool(payload.get("active_fea_job_id")),
        "last_update": payload.get("source_timestamp") or payload.get("ingest_timestamp"),
        "quality": payload.get("quality"),
        "text": style["text"],
        "indicator": style["indicator"],
        "color": style["color"],
        "backend_status": "ONLINE" if backend_online else "OFFLINE",
        "display_only": True,
        "stale": not backend_online,
    }


def apply_status_attributes(current: dict, view: dict) -> dict:
    """Return USD custom attribute updates. Does not compute a safety decision."""
    updated = dict(current)
    updated["coldDrawing:verdict"] = view.get("latest_verdict") or ""
    updated["coldDrawing:quality"] = view.get("quality") or ""
    updated["coldDrawing:feaRunning"] = "true" if view.get("fea_running") else "false"
    updated["coldDrawing:lastUpdate"] = view.get("last_update") or ""
    updated["coldDrawing:indicator"] = view.get("indicator") or NEUTRAL_INDICATOR
    updated["coldDrawing:backendStatus"] = view.get("backend_status") or "OFFLINE"
    return updated


def status_indicator_prim(usd_prim: str) -> str:
    return f"{usd_prim.rstrip('/')}/StatusIndicator"


def fea_lifecycle_label(job_status: str | None, *, active: bool) -> str:
    if not job_status:
        return "IDLE"
    mapping = {
        "QUEUED": "QUEUED",
        "RUNNING": "RUNNING",
        "SUCCEEDED": "COMPLETED",
        "FINALIZED": "COMPLETED",
        "FAILED": "FAILED",
        "TIMEOUT": "TIMEOUT",
        "CANCELLED": "FAILED",
        "PENDING": "QUEUED",
        "POSTPROCESSING": "RUNNING",
    }
    if not active and job_status in {"QUEUED", "RUNNING", "PENDING", "POSTPROCESSING"}:
        return mapping.get(job_status, "IDLE")
    return mapping.get(job_status, dash(job_status))


def panel_model(live: dict | None, *, backend_online: bool = True) -> dict[str, Any]:
    """Convert a backend live payload into the Omniverse / inspector panel model."""
    payload = live or {}
    process = payload.get("process") or {}
    decision = payload.get("decision") or {}
    fea = payload.get("fea") or {}
    features = process.get("features") or payload.get("features") or {}
    view = operator_view(
        {
            "asset_id": payload.get("asset_id"),
            "features": features,
            "latest_verdict": decision.get("latest_verdict") or payload.get("latest_verdict"),
            "latest_evaluation_id": decision.get("evaluation_id") or payload.get("latest_evaluation_id"),
            "latest_snapshot_id": decision.get("snapshot_id") or payload.get("latest_snapshot_id"),
            "latest_decision_id": decision.get("decision_id") or payload.get("latest_decision_id"),
            "routing_action": decision.get("routing_action"),
            "model_version": decision.get("model_version"),
            "active_fea_job_id": decision.get("fea_job_id") or payload.get("active_fea_job_id"),
            "source_timestamp": process.get("source_timestamp") or payload.get("source_timestamp"),
            "quality": process.get("quality") or payload.get("quality"),
        },
        backend_online=backend_online,
    )
    fea_status = "IDLE"
    if backend_online:
        fea_status = fea.get("status") or fea_lifecycle_label(
            fea.get("job_status"),
            active=bool(payload.get("active_fea_job_id") or decision.get("fea_job_id")),
        )
    return {
        **view,
        "state_version": dash(process.get("state_version") or payload.get("state_version")),
        "source_timestamp": dash(process.get("source_timestamp") or payload.get("source_timestamp")),
        "source_quality": dash(process.get("quality") or payload.get("quality")),
        "reduction_ratio": dash(features.get("reduction_ratio")),
        "die_half_angle_rad": dash(features.get("die_half_angle_rad")),
        "friction_coefficient": dash(features.get("friction_coefficient")),
        "normalized_hardening_coefficient": dash(features.get("normalized_hardening_coefficient")),
        "evaluation_id": dash(view.get("evaluation_id")),
        "snapshot_id": dash(view.get("snapshot_id")),
        "decision_id": dash(view.get("decision_id")),
        "routing_action": dash(view.get("routing_action")),
        "model_version": dash(view.get("model_version")),
        "fea_job_id": dash(view.get("fea_job_id")),
        "fea_status": fea_status if backend_online else UNAVAILABLE,
        "solver": dash(fea.get("solver")) if backend_online else UNAVAILABLE,
        "solver_version": dash(fea.get("solver_version")) if backend_online else UNAVAILABLE,
        "criterion_verdict": dash(fea.get("criterion_verdict")) if backend_online else UNAVAILABLE,
        "fea_quality": dash(fea.get("quality")) if backend_online else UNAVAILABLE,
        "last_completed_fea_job_id": dash(fea.get("last_completed_fea_job_id") or payload.get("last_completed_fea_job_id")),
        "usd_prim": payload.get("usd_prim") or "",
        "latest_verdict_label": dash(view.get("latest_verdict")),
    }
