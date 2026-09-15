from cold_drawing_twin.display import attach_current_analysis, inspector_analysis_cards


def _running_view():
    return {
        "evaluation": {
            "latestDecisionId": "dec-previous",
            "latestEvaluationId": "eval-previous",
            "latestSnapshotId": "snap-previous",
            "latestVerdict": "SAFE",
        },
        "simulation": {
            "activeFeaJobId": "fea-current",
            "lastCompletedFeaJobId": "fea-previous",
        },
        "current_analysis": {
            "evaluation_id": "eval-current",
            "snapshot_id": "snap-current",
            "fea_job_id": "fea-current",
            "routing": "REQUIRES_FEA",
        },
    }


def test_active_fea_does_not_expose_previous_decision_as_current():
    cards = inspector_analysis_cards(_running_view())
    labels = [row["label"] for row in cards["current_rows"]]
    values = [row["value"] for row in cards["current_rows"]]
    assert cards["running"] is True
    assert cards["show_generic_decision"] is False
    assert cards["current_decision_id"] is None
    assert "Decision" not in labels
    assert "dec-previous" not in values
    assert cards["headline"] == "FEA RUNNING"


def test_active_fea_exposes_last_finalized_as_historical():
    cards = inspector_analysis_cards(_running_view())
    assert cards["last_finalized_verdict"] == "SAFE"
    assert cards["last_finalized_decision_id"] == "dec-previous"
    assert ("Evaluation", "eval-current") in [(row["label"], row["value"]) for row in cards["current_rows"]]
    assert ("Snapshot", "snap-current") in [(row["label"], row["value"]) for row in cards["current_rows"]]
    sim = [(row["label"], row["value"]) for row in cards["sim_rows"]]
    assert ("Active FEA", "fea-current") in sim
    assert ("Last completed", "fea-previous") in sim


def test_finalized_shows_current_decision_normally():
    cards = inspector_analysis_cards(
        {
            "evaluation": {
                "latestDecisionId": "dec-current",
                "latestEvaluationId": "eval-current",
                "latestSnapshotId": "snap-current",
                "latestVerdict": "INCONCLUSIVE",
            },
            "simulation": {
                "activeFeaJobId": None,
                "lastCompletedFeaJobId": "fea-current",
            },
        }
    )
    assert cards["running"] is False
    assert cards["finalized"] is True
    assert cards["show_generic_decision"] is True
    assert cards["headline"] == "MANUAL REVIEW"
    assert cards["engineering_note"] == "Engineering verdict  INCONCLUSIVE"
    assert cards["current_decision_id"] == "dec-current"
    assert cards["last_finalized_decision_id"] is None
    assert cards["current_rows"][0] == {
        "key": "latestDecisionId",
        "label": "Decision",
        "value": "dec-current",
    }


def test_fast_safe_shows_current_decision_normally():
    cards = inspector_analysis_cards(
        {
            "evaluation": {
                "latestDecisionId": "dec-current",
                "latestEvaluationId": "eval-current",
                "latestSnapshotId": "snap-current",
                "latestVerdict": "SAFE",
            },
            "simulation": {"activeFeaJobId": None, "lastCompletedFeaJobId": "fea-old"},
        }
    )
    assert cards["fast_path"] is True
    assert cards["running"] is False
    assert cards["show_generic_decision"] is True
    assert cards["headline"] == "SAFE"
    assert cards["current_decision_id"] == "dec-current"
    assert cards["last_finalized_decision_id"] is None
    assert cards["current_rows"][0]["label"] == "Decision"
    assert cards["sim_rows"][0]["label"] == "Active FEA"


def test_attach_current_analysis_does_not_rewrite_basyx_evaluation():
    view = {
        "evaluation": {
            "latestDecisionId": "dec-previous",
            "latestEvaluationId": "eval-previous",
            "latestSnapshotId": "snap-previous",
            "latestVerdict": "SAFE",
        },
        "simulation": {"activeFeaJobId": "fea-current", "lastCompletedFeaJobId": "fea-previous"},
    }
    live = {
        "decision": {"decision_id": "dec-previous", "fea_job_id": "fea-current"},
        "fea": {
            "active_evaluation_id": "eval-current",
            "active_snapshot_id": "snap-current",
        },
    }
    out = attach_current_analysis(view, live)
    assert out["evaluation"]["latestDecisionId"] == "dec-previous"
    assert out["evaluation"]["latestEvaluationId"] == "eval-previous"
    assert out["evaluation"]["latestVerdict"] == "SAFE"
    assert out["current_analysis"]["evaluation_id"] == "eval-current"
    assert out["current_analysis"]["snapshot_id"] == "snap-current"
    assert out["current_analysis"]["routing"] == "REQUIRES_FEA"
    assert out["display"]["show_generic_decision"] is False
    assert out["display"]["current_decision_id"] is None
    assert "Decision" not in [row["label"] for row in out["display"]["current_rows"]]
