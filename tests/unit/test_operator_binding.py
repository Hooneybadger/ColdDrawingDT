from cold_drawing_twin.display import apply_status_attributes, operator_view


def test_operator_view_is_display_only():
    view = operator_view(
        {
            "asset_id": "BG.MIEUM.DRW.04",
            "features": {"reduction_ratio": 0.3},
            "latest_verdict": "SAFE",
            "active_fea_job_id": None,
            "source_timestamp": "2026-08-01T00:00:00Z",
            "quality": "GOOD",
        }
    )
    assert view["display_only"] is True
    assert view["fea_running"] is False
    assert view["latest_verdict"] == "SAFE"
    attrs = apply_status_attributes({}, view)
    assert attrs["coldDrawing:verdict"] == "SAFE"
    assert attrs["coldDrawing:quality"] == "GOOD"
