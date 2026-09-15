from cold_drawing_twin.display import (
    ATTENTION_ADVISORY,
    ATTENTION_ALARM,
    ATTENTION_NONE,
    ATTENTION_UNAVAILABLE,
    ATTENTION_WARNING,
    NEUTRAL_INDICATOR,
    apply_status_attributes,
    attention_level,
    operator_view,
    panel_model,
    status_indicator_prim,
    status_tower_prim,
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
    assert view["attention"] == ATTENTION_NONE
    assert view["process_variables"][0]["key"] == "reduction_ratio"
    assert view["process_variables"][0]["value"] == "0.3"
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
    assert status_tower_prim(model["usd_prim"]).endswith("Drawing_04/StatusTower")
    assert model["fea_headline"] == "NOT REQUIRED"


def test_panel_model_offline_is_neutral():
    model = panel_model({"decision": {"latest_verdict": "UNSAFE"}}, backend_online=False)
    assert model["backend_status"] == "OFFLINE"
    assert model["latest_verdict"] is None
    assert model["indicator"] == NEUTRAL_INDICATOR
    assert model["latest_verdict_label"] == "—"
    assert model["attention"] == ATTENTION_UNAVAILABLE


def test_attention_follows_isa101_exceptionalism():
    assert attention_level("SAFE") == ATTENTION_NONE
    assert attention_level("UNSAFE") == ATTENTION_ALARM
    assert attention_level("INCONCLUSIVE") == ATTENTION_WARNING
    assert attention_level("MANUAL_REVIEW") == ATTENTION_WARNING
    assert attention_level("ANALYSIS_REQUIRED") == ATTENTION_ADVISORY
    assert attention_level("SAFE", fea_status="RUNNING") == ATTENTION_ADVISORY
    assert attention_level("UNSAFE", fea_status="RUNNING") == ATTENTION_ALARM
    assert attention_level("SAFE", backend_online=False) == ATTENTION_UNAVAILABLE
    assert attention_level(None) == ATTENTION_UNAVAILABLE
    assert attention_level("NOT_A_VERDICT") == ATTENTION_UNAVAILABLE


def test_panel_model_running_fea_is_advisory_not_a_verdict():
    model = panel_model(
        {
            "asset_id": "BG.MIEUM.DRW.04",
            "decision": {"latest_verdict": "SAFE", "decision_id": "dec-1"},
            "fea": {"status": "RUNNING"},
        }
    )
    assert model["latest_verdict"] == "SAFE"
    assert model["indicator"] == "blue"
    assert model["attention"] == ATTENTION_ADVISORY
    assert model["fea_status"] == "RUNNING"
    assert model["headline"] == "WAITING FOR FEA"
    assert model["show_last_finalized"] is True
    assert model["fea_headline"] == "RUNNING"
    assert model["current_route"] == "REQUIRES_FEA"
    assert model["text"] == "Engineering decision pending."
    assert "continue" not in model["text"].lower()
    assert model["last_finalized_verdict"] == "SAFE"
    assert model["decision_id"] == "dec-1"


def test_panel_model_running_uses_active_job_lineage():
    model = panel_model(
        {
            "asset_id": "BG.MIEUM.DRW.04",
            "decision": {
                "latest_verdict": "SAFE",
                "decision_id": "dec-old",
                "evaluation_id": "eval-old",
                "snapshot_id": "snap-old",
                "routing_action": "ACCEPT",
                "fea_job_id": "fea-run",
                "model_version": "v0.1.1",
            },
            "fea": {
                "status": "RUNNING",
                "solver": "OpenRadioss",
                "active_evaluation_id": "eval-now",
                "active_snapshot_id": "snap-now",
            },
        }
    )
    assert model["headline"] == "WAITING FOR FEA"
    assert model["show_last_finalized"] is True
    assert model["evaluation_id"] == "eval-now"
    assert model["snapshot_id"] == "snap-now"
    assert model["decision_id"] == "dec-old"
    assert model["last_finalized_verdict"] == "SAFE"
    assert model["fea_headline"] == "RUNNING"
    assert model["current_route"] == "REQUIRES_FEA"
    assert model["indicator"] == "blue"


def test_panel_model_safe_hides_historical_fea():
    model = panel_model(
        {
            "asset_id": "BG.MIEUM.DRW.04",
            "decision": {
                "latest_verdict": "SAFE",
                "routing_action": "ACCEPT",
                "decision_id": "dec-new",
                "fea_job_id": None,
            },
            "fea": {"status": "COMPLETED", "last_completed_fea_job_id": "fea-old", "solver": "OpenRadioss"},
        }
    )
    assert model["latest_verdict"] == "SAFE"
    assert model["indicator"] == "green"
    assert model["fea_headline"] == "NOT REQUIRED"
    assert model["fea_status"] == "NOT REQUIRED"
    assert model["fea_job_id"] == "—"
    assert model["history_fea_job_id"] == "fea-old"
    assert model["solver"] == "—"
    assert model["show_last_finalized"] is False
    assert model["last_finalized_verdict"] == "—"


def test_panel_model_inconclusive_separates_completed_fea():
    model = panel_model(
        {
            "asset_id": "BG.MIEUM.DRW.04",
            "decision": {
                "latest_verdict": "INCONCLUSIVE",
                "routing_action": "REQUIRES_FEA",
                "decision_id": "dec-new",
                "fea_job_id": "fea-now",
            },
            "fea": {
                "status": "COMPLETED",
                "last_completed_fea_job_id": "fea-now",
                "solver": "OpenRadioss",
                "quality": "PASS",
                "criterion_verdict": "INCONCLUSIVE",
            },
        }
    )
    assert model["headline"] == "MANUAL REVIEW"
    assert model["engineering_verdict"] == "INCONCLUSIVE"
    assert model["fea_headline"] == "COMPLETED"
    assert model["evaluation_status"] == "MANUAL REVIEW"
    assert model["fea_job_id"] == "fea-now"
    assert model["fea_quality"] == "PASS"
    assert model["criterion_verdict"] == "INCONCLUSIVE"
    assert model["show_last_finalized"] is False
    assert model["indicator"] == "amber"
    assert model["last_finalized_verdict"] == "—"
