from cold_drawing_twin.display import ATTENTION_NONE, panel_model
from cold_drawing_twin.kit_panel import LivePanel


class _Ctx:
    def __init__(self, *args, **kwargs):
        self.collapsed = kwargs.get("collapsed", False)
        self.args = args
        self.kwargs = kwargs

    def __call__(self, *args, **kwargs):
        nested = _Ctx(*args, **kwargs)
        nested.collapsed = kwargs.get("collapsed", False)
        return nested

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class FakeWindow(_Ctx):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.frame = _Ctx()


class FakeLabel:
    def __init__(self, text="", **kwargs):
        self.text = text
        self.style = kwargs.get("style") or {}
        self.visible = True


class FakeUi:
    Window = FakeWindow
    ScrollingFrame = _Ctx
    VStack = _Ctx
    HStack = _Ctx
    Spacer = _Ctx
    CollapsableFrame = _Ctx
    Label = FakeLabel


def test_live_panel_faceplate_shows_verdict_and_lineage():
    panel = LivePanel("Cold Drawing Operator", FakeUi)
    model = panel_model(
        {
            "asset_id": "BG.MIEUM.DRW.04",
            "process": {
                "features": {"reduction_ratio": 0.3, "die_half_angle_rad": 0.2},
                "source_timestamp": "2026-08-01T00:00:00Z",
                "quality": "GOOD",
            },
            "decision": {
                "latest_verdict": "SAFE",
                "decision_id": "dec-1",
                "evaluation_id": "eval-1",
                "snapshot_id": "snap-1",
            },
            "fea": {"status": "IDLE"},
        }
    )
    panel.apply(model)
    assert panel.verdict.text == "SAFE"
    assert panel.decision_heading.text == "DECISION"
    assert panel.decision_id.text.startswith("Decision")
    assert "dec-1" in panel.decision_id.text
    assert panel._pv_labels[0][1].text == "0.3"
    assert model["attention"] == ATTENTION_NONE
    assert panel.banner.text == ""
    assert "NOT REQUIRED" in panel.fea_status.text
    assert panel.quality.text == ""
    assert panel.criterion.text == ""


def test_live_panel_running_separates_last_decision():
    panel = LivePanel("Cold Drawing Operator", FakeUi)
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
    panel.apply(model)
    assert panel.verdict.text == "WAITING FOR FEA"
    assert "RUNNING" in panel.fea_status.text
    assert "fea-run" in panel.fea_job.text
    assert "OpenRadioss" in panel.solver.text
    assert panel.decision_heading.text == "LAST FINALIZED DECISION"
    assert panel.decision_heading.text != "DECISION"
    assert not panel.decision_id.text.startswith("Decision")
    assert "SAFE" in panel.decision_id.text
    assert "dec-old" in panel.decision_id.text
    assert panel.last_finalized.text == ""
    assert panel.last_fea.text == ""
    assert panel.banner.text == "Engineering decision pending."
    assert "continue" not in panel.banner.text.lower()
    assert "Status" in panel.eval_status.text
    assert "WAITING FOR FEA" in panel.eval_status.text
    assert "eval-now" in panel.evaluation_id.text
    assert "snap-now" in panel.snapshot_id.text
    assert "REQUIRES_FEA" in panel.routing.text
    assert "v0.1.1" in panel.model.text


def test_live_panel_inconclusive_is_manual_review():
    panel = LivePanel("Cold Drawing Operator", FakeUi)
    model = panel_model(
        {
            "asset_id": "BG.MIEUM.DRW.04",
            "decision": {
                "latest_verdict": "INCONCLUSIVE",
                "decision_id": "dec-new",
                "routing_action": "REQUIRES_FEA",
                "fea_job_id": "fea-now",
            },
            "fea": {
                "status": "COMPLETED",
                "last_completed_fea_job_id": "fea-now",
                "quality": "PASS",
                "criterion_verdict": "INCONCLUSIVE",
            },
        }
    )
    panel.apply(model)
    assert panel.verdict.text == "MANUAL REVIEW"
    assert panel.decision_heading.text == "DECISION"
    assert panel.decision_id.text.startswith("Decision")
    assert "dec-new" in panel.decision_id.text
    assert "INCONCLUSIVE" in panel.banner.text
    assert panel.fea_status.text == "COMPLETED"
    assert "PASS" in panel.quality.text
    assert "INCONCLUSIVE" in panel.criterion.text


def test_live_panel_hides_unset_solver_version():
    panel = LivePanel("Cold Drawing Operator", FakeUi)
    model = panel_model(
        {
            "asset_id": "BG.MIEUM.DRW.04",
            "decision": {
                "latest_verdict": "SAFE",
                "routing_action": "REQUIRES_FEA",
                "fea_job_id": "fea-run",
            },
            "fea": {"status": "RUNNING", "solver_version": None},
        }
    )
    panel.apply(model)
    assert panel.verdict.text == "WAITING FOR FEA"
    assert panel.solver_version.text == ""
