from cold_drawing_twin.display import (
    NEUTRAL_INDICATOR,
    apply_status_attributes,
    operator_view,
    panel_model,
    status_indicator_prim,
    verdict_style,
)


def test_operator_view_is_display_only():
    view = operator_view(
        {
            "asset_id": "BG.MIEUM.DRW.04",
            "features": {"reduction_ratio": 0.3},
            "latest_verdict": "SAFE",
            "latest_decision_id": "dec-0001",
            "active_fea_job_id": None,
            "source_timestamp": "2026-08-01T00:00:00Z",
            "quality": "GOOD",
        }
    )
    assert view["display_only"] is True
    assert view["fea_running"] is False
    assert view["latest_verdict"] == "SAFE"
    assert view["decision_id"] == "dec-0001"
    assert view["backend_status"] == "ONLINE"
    attrs = apply_status_attributes({}, view)
    assert attrs["coldDrawing:verdict"] == "SAFE"
    assert attrs["coldDrawing:quality"] == "GOOD"
    assert attrs["coldDrawing:indicator"] == "green"


def test_verdict_colors_and_unknown_are_neutral():
    assert verdict_style("SAFE")["indicator"] == "green"
    assert verdict_style("UNSAFE")["indicator"] == "red"
    assert verdict_style("ANALYSIS_REQUIRED")["indicator"] == "blue"
    assert verdict_style("INCONCLUSIVE")["indicator"] == "amber"
    assert verdict_style("MANUAL_REVIEW")["indicator"] == "amber"
    assert verdict_style(None)["indicator"] == NEUTRAL_INDICATOR
    assert verdict_style("NOT_A_VERDICT")["indicator"] == NEUTRAL_INDICATOR
    offline = verdict_style("SAFE", backend_online=False)
    assert offline["indicator"] == NEUTRAL_INDICATOR
    assert offline["verdict"] is None


def test_backend_offline_does_not_invent_analysis_required():
    view = operator_view(
        {"asset_id": "BG.MIEUM.DRW.04", "latest_verdict": "SAFE"},
        backend_online=False,
    )
    assert view["backend_status"] == "OFFLINE"
    assert view["latest_verdict"] is None
    assert view["indicator"] == NEUTRAL_INDICATOR
    assert view["latest_verdict"] != "ANALYSIS_REQUIRED"
    assert "OFFLINE" in view["text"]


def test_missing_verdict_is_not_analysis_required():
    view = operator_view({"asset_id": "BG.MIEUM.DRW.04"})
    assert view["backend_status"] == "ONLINE"
    assert view["latest_verdict"] is None
    assert view["indicator"] == NEUTRAL_INDICATOR


def test_panel_model_exposes_lineage_ids():
    model = panel_model(
        {
            "asset_id": "BG.MIEUM.DRW.04",
            "usd_prim": "/World/BugokFactory/Production/Drawing/Drawing_04",
            "process": {
                "features": {
                    "reduction_ratio": 0.3,
                    "die_half_angle_rad": 0.2,
                    "friction_coefficient": 0.08,
                    "normalized_hardening_coefficient": 0.7,
                },
                "state_version": "state-0001",
                "source_timestamp": "2026-08-01T00:00:00Z",
                "quality": "GOOD",
            },
            "decision": {
                "latest_verdict": "SAFE",
                "evaluation_id": "eval-1",
                "snapshot_id": "snap-1",
                "decision_id": "dec-1",
                "routing_action": "ACCEPT",
                "model_version": "v0.1.1",
                "fea_job_id": None,
            },
            "fea": {"status": "IDLE"},
        }
    )
    assert model["decision_id"] == "dec-1"
    assert model["evaluation_id"] == "eval-1"
    assert model["snapshot_id"] == "snap-1"
    assert model["latest_verdict"] == "SAFE"
    assert model["indicator"] == "green"
    assert status_indicator_prim(model["usd_prim"]).endswith("Drawing_04/StatusIndicator")


def test_panel_model_offline_is_neutral():
    model = panel_model({"decision": {"latest_verdict": "UNSAFE"}}, backend_online=False)
    assert model["backend_status"] == "OFFLINE"
    assert model["latest_verdict"] is None
    assert model["indicator"] == NEUTRAL_INDICATOR
    assert model["latest_verdict_label"] == "—"
