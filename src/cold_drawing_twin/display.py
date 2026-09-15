from __future__ import annotations

from typing import Any

UNAVAILABLE = "—"
NEUTRAL_INDICATOR = "gray"
NEUTRAL_COLOR = (0.45, 0.45, 0.45)

ATTENTION_NONE = "none"
ATTENTION_ADVISORY = "advisory"
ATTENTION_WARNING = "warning"
ATTENTION_ALARM = "alarm"
ATTENTION_UNAVAILABLE = "unavailable"

PROCESS_VARIABLES = (
    {"key": "reduction_ratio", "label": "Reduction ratio", "unit": ""},
    {"key": "die_half_angle_rad", "label": "Die half angle", "unit": "rad"},
    {"key": "friction_coefficient", "label": "Friction coefficient", "unit": ""},
    {
        "key": "normalized_hardening_coefficient",
        "label": "Norm. hardening",
        "unit": "",
    },
)

VERDICT_DISPLAY = {
    "SAFE": {
        "text": "Continue the current pass.",
        "indicator": "green",
        "color": (0.12, 0.72, 0.20),
    },
    "UNSAFE": {
        "text": "Stop. Condition rejected.",
        "indicator": "red",
        "color": (0.86, 0.10, 0.10),
    },
    "INCONCLUSIVE": {
        "text": "Wait for review.",
        "indicator": "amber",
        "color": (0.92, 0.68, 0.08),
    },
    "MANUAL_REVIEW": {
        "text": "Wait for review.",
        "indicator": "amber",
        "color": (0.85, 0.60, 0.10),
    },
    "ANALYSIS_REQUIRED": {
        "text": "Check in progress.",
        "indicator": "blue",
        "color": (0.16, 0.48, 0.90),
    },
}


def dash(value: Any) -> str:
    if value is None or value == "":
        return UNAVAILABLE
    return str(value)


def format_process_value(value: Any) -> str:
    if value is None or value == "":
        return UNAVAILABLE
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, int) and not isinstance(value, bool):
        return str(value)
    if isinstance(value, float):
        return f"{value:.4g}"
    return str(value)


def process_variable_rows(features: dict | None) -> list[dict[str, str]]:
    payload = features or {}
    rows = []
    for item in PROCESS_VARIABLES:
        rows.append(
            {
                "key": item["key"],
                "label": item["label"],
                "unit": item["unit"],
                "value": format_process_value(payload.get(item["key"])),
            }
        )
    return rows


def attention_level(
    verdict: str | None,
    *,
    backend_online: bool = True,
    fea_status: str | None = None,
) -> str:
    """ISA-101-style attention for chrome. Does not change the stored verdict."""
    if not backend_online:
        return ATTENTION_UNAVAILABLE
    if verdict == "UNSAFE":
        return ATTENTION_ALARM
    status = (fea_status or "").upper()
    if status in {"QUEUED", "RUNNING"}:
        return ATTENTION_ADVISORY
    if verdict in {"INCONCLUSIVE", "MANUAL_REVIEW"}:
        return ATTENTION_WARNING
    if verdict == "ANALYSIS_REQUIRED":
        return ATTENTION_ADVISORY
    if not verdict or verdict not in VERDICT_DISPLAY:
        return ATTENTION_UNAVAILABLE
    return ATTENTION_NONE


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
    features = payload.get("features") or {}
    style = verdict_style(payload.get("latest_verdict"), backend_online=backend_online)
    fea_status = payload.get("fea_status")
    status = (fea_status or "").upper()
    busy = backend_online and status in {"QUEUED", "RUNNING", "PENDING", "POSTPROCESSING"}
    if busy:
        analysis = VERDICT_DISPLAY["ANALYSIS_REQUIRED"]
        style = {
            **style,
            "text": "Engineering decision pending.",
            "indicator": analysis["indicator"],
            "color": analysis["color"],
        }
    return {
        "asset_id": payload.get("asset_id"),
        "process_state": features,
        "process_variables": process_variable_rows(features),
        "attention": attention_level(
            style["verdict"],
            backend_online=backend_online,
            fea_status=fea_status,
        ),
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


def status_tower_prim(usd_prim: str) -> str:
    return f"{usd_prim.rstrip('/')}/StatusTower"


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


def short_id(value: Any, keep: int = 10) -> str:
    text = dash(value)
    if text == UNAVAILABLE or len(text) <= keep + 1:
        return text
    return text[:keep] + "..."


def panel_fea_semantics(
    *,
    routing: str | None,
    verdict: str | None,
    fea_status: str | None,
    last_completed: str | None,
    decision_fea_job: str | None,
    active_job: bool,
) -> dict[str, Any]:
    """Separate current Evaluation/FEA from leftover Twin history. Display only."""
    status = (fea_status or "").upper()
    busy = active_job or status in {"QUEUED", "RUNNING"}
    if busy:
        route = routing if routing and routing not in {"ACCEPT"} else "REQUIRES_FEA"
        return {
            "fea_headline": status if status in {"QUEUED", "RUNNING"} else "RUNNING",
            "evaluation_status": "WAITING FOR FEA",
            "current_route": route,
            "headline": "WAITING FOR FEA",
            "engineering_verdict": dash(verdict),
            "show_last_finalized": True,
            "current_fea_job_id": dash(decision_fea_job),
            "history_fea_job_id": dash(last_completed) if last_completed and last_completed != decision_fea_job else UNAVAILABLE,
        }
    if verdict in {"INCONCLUSIVE", "MANUAL_REVIEW"}:
        return {
            "fea_headline": "COMPLETED",
            "evaluation_status": "MANUAL REVIEW",
            "current_route": routing or "REQUIRES_FEA",
            "headline": "MANUAL REVIEW",
            "engineering_verdict": dash(verdict),
            "show_last_finalized": False,
            "current_fea_job_id": dash(decision_fea_job or last_completed),
            "history_fea_job_id": UNAVAILABLE,
        }
    if routing == "ACCEPT" or verdict in {"SAFE", "UNSAFE"}:
        return {
            "fea_headline": "NOT REQUIRED",
            "evaluation_status": "",
            "current_route": routing or ("ACCEPT" if verdict == "SAFE" else dash(routing)),
            "headline": dash(verdict),
            "engineering_verdict": dash(verdict),
            "show_last_finalized": False,
            "current_fea_job_id": UNAVAILABLE,
            "history_fea_job_id": dash(last_completed),
        }
    return {
        "fea_headline": dash(status) if status else UNAVAILABLE,
        "evaluation_status": "",
        "current_route": dash(routing),
        "headline": dash(verdict),
        "engineering_verdict": dash(verdict),
        "show_last_finalized": False,
        "current_fea_job_id": dash(decision_fea_job),
        "history_fea_job_id": dash(last_completed),
    }


def panel_model(live: dict | None, *, backend_online: bool = True) -> dict[str, Any]:
    """Convert a backend live payload into the Omniverse / inspector panel model."""
    payload = live or {}
    process = payload.get("process") or {}
    decision = payload.get("decision") or {}
    fea = payload.get("fea") or {}
    features = process.get("features") or payload.get("features") or {}
    fea_status = "IDLE"
    if backend_online:
        fea_status = fea.get("status") or fea_lifecycle_label(
            fea.get("job_status"),
            active=bool(payload.get("active_fea_job_id") or decision.get("fea_job_id")),
        )
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
            "fea_status": fea_status if backend_online else None,
        },
        backend_online=backend_online,
    )
    semantics = panel_fea_semantics(
        routing=decision.get("routing_action"),
        verdict=view.get("latest_verdict"),
        fea_status=fea_status if backend_online else None,
        last_completed=fea.get("last_completed_fea_job_id") or payload.get("last_completed_fea_job_id"),
        decision_fea_job=decision.get("fea_job_id"),
        active_job=fea_status in {"QUEUED", "RUNNING"},
    )
    evaluation_id = dash(view.get("evaluation_id"))
    snapshot_id = dash(view.get("snapshot_id"))
    if semantics.get("show_last_finalized"):
        if fea.get("active_evaluation_id"):
            evaluation_id = dash(fea.get("active_evaluation_id"))
        if fea.get("active_snapshot_id"):
            snapshot_id = dash(fea.get("active_snapshot_id"))
    last_finalized_verdict = dash(decision.get("latest_verdict") or view.get("latest_verdict"))
    if not semantics.get("show_last_finalized"):
        last_finalized_verdict = UNAVAILABLE
    return {
        **view,
        **semantics,
        "title": "DRAWING 04",
        "state_version": dash(process.get("state_version") or payload.get("state_version")),
        "source_timestamp": dash(process.get("source_timestamp") or payload.get("source_timestamp")),
        "source_quality": dash(process.get("quality") or payload.get("quality")),
        "reduction_ratio": dash(features.get("reduction_ratio")),
        "die_half_angle_rad": dash(features.get("die_half_angle_rad")),
        "friction_coefficient": dash(features.get("friction_coefficient")),
        "normalized_hardening_coefficient": dash(features.get("normalized_hardening_coefficient")),
        "evaluation_id": evaluation_id,
        "snapshot_id": snapshot_id,
        "decision_id": dash(view.get("decision_id")),
        "last_finalized_verdict": last_finalized_verdict,
        "routing_action": dash(semantics.get("current_route") or view.get("routing_action")),
        "model_version": dash(view.get("model_version")),
        "fea_job_id": semantics["current_fea_job_id"],
        "fea_status": semantics["fea_headline"] if backend_online else UNAVAILABLE,
        "solver": dash(fea.get("solver")) if backend_online and semantics["fea_headline"] != "NOT REQUIRED" else UNAVAILABLE,
        "solver_version": dash(fea.get("solver_version")) if backend_online and semantics["fea_headline"] != "NOT REQUIRED" else UNAVAILABLE,
        "criterion_verdict": dash(fea.get("criterion_verdict")) if backend_online and semantics["fea_headline"] != "NOT REQUIRED" else UNAVAILABLE,
        "fea_quality": dash(fea.get("quality")) if backend_online and semantics["fea_headline"] != "NOT REQUIRED" else UNAVAILABLE,
        "last_completed_fea_job_id": semantics["history_fea_job_id"],
        "usd_prim": payload.get("usd_prim") or "",
        "latest_verdict_label": dash(view.get("latest_verdict")),
        "headline": semantics["headline"] if backend_online else "OFFLINE",
        "engineering_verdict": semantics.get("engineering_verdict") or dash(view.get("latest_verdict")),
    }


def attach_current_analysis(view: dict, live: dict | None) -> dict[str, Any]:
    """Overlay Twin current-job IDs for Inspector display. Does not rewrite BaSyx EvaluationState."""
    updated = dict(view)
    simulation = view.get("simulation") or {}
    current = None
    if simulation.get("activeFeaJobId"):
        fea = (live or {}).get("fea") or {}
        decision = (live or {}).get("decision") or {}
        current = {
            "evaluation_id": fea.get("active_evaluation_id"),
            "snapshot_id": fea.get("active_snapshot_id"),
            "fea_job_id": decision.get("fea_job_id") or simulation.get("activeFeaJobId"),
            "routing": "REQUIRES_FEA",
        }
    updated["current_analysis"] = current
    updated["display"] = inspector_analysis_cards(updated)
    return updated


def inspector_analysis_cards(view: dict) -> dict[str, Any]:
    """Inspector presentation only. Latest BaSyx Decision is historical while FEA is active."""
    evaluation = view.get("evaluation") or {}
    simulation = view.get("simulation") or {}
    current = view.get("current_analysis") or {}
    running = bool(simulation.get("activeFeaJobId"))
    verdict = evaluation.get("latestVerdict")
    evaluation_rows = [
        {"key": "latestDecisionId", "label": "Decision", "value": evaluation.get("latestDecisionId")},
        {"key": "latestEvaluationId", "label": "Evaluation", "value": evaluation.get("latestEvaluationId")},
        {"key": "latestSnapshotId", "label": "Snapshot", "value": evaluation.get("latestSnapshotId")},
    ]
    if running:
        return {
            "running": True,
            "finalized": False,
            "fast_path": False,
            "title": "Current Analysis",
            "headline": "FEA RUNNING",
            "engineering_note": "",
            "sim_note": "FEA RUNNING",
            "current_rows": [
                {"key": "evaluation_id", "label": "Evaluation", "value": current.get("evaluation_id")},
                {"key": "snapshot_id", "label": "Snapshot", "value": current.get("snapshot_id")},
                {"key": "routing", "label": "Route", "value": current.get("routing") or "REQUIRES_FEA"},
            ],
            "show_generic_decision": False,
            "current_decision_id": None,
            "last_finalized_verdict": verdict,
            "last_finalized_decision_id": evaluation.get("latestDecisionId"),
            "sim_rows": [
                {"key": "activeFeaJobId", "label": "Active FEA", "value": simulation.get("activeFeaJobId")},
                {
                    "key": "lastCompletedFeaJobId",
                    "label": "Last completed",
                    "value": simulation.get("lastCompletedFeaJobId"),
                },
            ],
        }
    if verdict in {"INCONCLUSIVE", "MANUAL_REVIEW"}:
        return {
            "running": False,
            "finalized": True,
            "fast_path": False,
            "title": "Evaluation",
            "headline": "MANUAL REVIEW",
            "engineering_note": "Engineering verdict  INCONCLUSIVE",
            "sim_note": "FEA COMPLETED",
            "current_rows": evaluation_rows,
            "show_generic_decision": True,
            "current_decision_id": evaluation.get("latestDecisionId"),
            "last_finalized_verdict": None,
            "last_finalized_decision_id": None,
            "sim_rows": [
                {"key": "activeFeaJobId", "label": "Active FEA", "value": simulation.get("activeFeaJobId")},
                {
                    "key": "lastCompletedFeaJobId",
                    "label": "Last completed",
                    "value": simulation.get("lastCompletedFeaJobId"),
                },
            ],
        }
    if verdict in {"SAFE", "UNSAFE"}:
        return {
            "running": False,
            "finalized": False,
            "fast_path": verdict == "SAFE",
            "title": "Evaluation",
            "headline": dash(verdict),
            "engineering_note": "",
            "sim_note": "",
            "current_rows": evaluation_rows,
            "show_generic_decision": True,
            "current_decision_id": evaluation.get("latestDecisionId"),
            "last_finalized_verdict": None,
            "last_finalized_decision_id": None,
            "sim_rows": [
                {"key": "activeFeaJobId", "label": "Active FEA", "value": simulation.get("activeFeaJobId")},
            ],
        }
    return {
        "running": False,
        "finalized": False,
        "fast_path": False,
        "title": "Evaluation",
        "headline": dash(verdict),
        "engineering_note": "",
        "sim_note": "",
        "current_rows": evaluation_rows,
        "show_generic_decision": True,
        "current_decision_id": evaluation.get("latestDecisionId"),
        "last_finalized_verdict": None,
        "last_finalized_decision_id": None,
        "sim_rows": [
            {"key": "activeFeaJobId", "label": "Active FEA", "value": simulation.get("activeFeaJobId")},
            {
                "key": "lastCompletedFeaJobId",
                "label": "Last completed",
                "value": simulation.get("lastCompletedFeaJobId"),
            },
        ],
    }
