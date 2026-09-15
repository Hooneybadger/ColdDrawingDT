from omniverse.scripts.render_evidence_cards import pinn_display, solver_html


OOD = {
    "process": {
        "features": {
            "reduction_ratio": 0.55,
            "die_half_angle_rad": 0.20,
            "friction_coefficient": 0.08,
            "normalized_hardening_coefficient": 0.70,
        }
    },
    "decision": {
        "latest_verdict": "INCONCLUSIVE",
        "routing_action": "REQUIRES_FEA",
        "model_version": "v0.1.1",
        "decision_id": "dec-x",
        "evaluation_id": "eval-x",
        "snapshot_id": "snap-x",
    },
    "fea": {
        "status": "COMPLETED",
        "quality": "PASS",
        "criterion_verdict": "INCONCLUSIVE",
        "last_completed_fea_job_id": "fea-x",
    },
}


def test_pinn_ood_evidence_is_need_fea_not_inconclusive():
    fields = pinn_display(
        OOD,
        {
            "pinn_result": {
                "verdict": "NEED_FEA",
                "supported_range": False,
                "model_version": "v0.1.1",
            },
            "routing_action": "REQUIRES_FEA",
        },
    )
    assert fields["model_result"] == "NEED_FEA"
    assert fields["supported_range"] == "NO"
    assert fields["routing"] == "REQUIRES_FEA"
    html = solver_html(OOD, {"pinn_result": {"verdict": "NEED_FEA", "supported_range": False}})
    pinn_block, fea_block = html.split("OpenRadioss", 1)
    assert "NEED_FEA" in pinn_block
    assert "Supported range" in pinn_block
    assert "INCONCLUSIVE" not in pinn_block
    assert "INCONCLUSIVE" in fea_block
    assert "MANUAL REVIEW" in fea_block
    assert "Automatic verdict disabled" in fea_block


def test_pinn_ood_does_not_copy_decision_verdict_when_pinn_missing():
    fields = pinn_display(OOD, {"routing_action": "REQUIRES_FEA"})
    assert fields["model_result"] == "NEED_FEA"
    assert fields["supported_range"] == "NO"
    assert fields["model_result"] != "INCONCLUSIVE"
