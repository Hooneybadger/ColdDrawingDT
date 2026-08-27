from __future__ import annotations

from typing import Any

from cold_drawing_twin.display import dash


class LivePanel:
    """omni.ui operator/senior panel. Display only."""

    def __init__(self, title: str, ui_module) -> None:
        ui = ui_module
        self._window = ui.Window(title, width=400, height=760)
        with self._window.frame:
            with ui.ScrollingFrame():
                with ui.VStack(spacing=6):
                    self.backend = ui.Label("Backend: —")
                    ui.Spacer(height=8)
                    ui.Label("PROCESS STATE")
                    self.asset_id = ui.Label("Asset ID: —")
                    self.reduction = ui.Label("Reduction Ratio: —")
                    self.die = ui.Label("Die Half Angle: —")
                    self.friction = ui.Label("Friction Coefficient: —")
                    self.hardening = ui.Label("Normalized Hardening Coefficient: —")
                    self.state_version = ui.Label("State Version: —")
                    self.source_ts = ui.Label("Source Timestamp: —")
                    self.source_quality = ui.Label("Source Quality: —")
                    ui.Spacer(height=8)
                    ui.Label("DECISION")
                    self.verdict = ui.Label("Latest Verdict: —")
                    self.evaluation_id = ui.Label("Evaluation ID: —")
                    self.snapshot_id = ui.Label("Snapshot ID: —")
                    self.decision_id = ui.Label("Decision ID: —")
                    self.routing = ui.Label("Routing Action: —")
                    self.model = ui.Label("Model Version: —")
                    self.fea_job = ui.Label("FEA Job ID: —")
                    ui.Spacer(height=8)
                    ui.Label("FEA")
                    self.fea_status = ui.Label("FEA Status: —")
                    self.solver = ui.Label("Solver: —")
                    self.solver_version = ui.Label("Solver Version: —")
                    self.criterion = ui.Label("Criterion Verdict: —")
                    self.quality = ui.Label("Quality: —")
                    self.last_fea = ui.Label("Last Completed FEA Job ID: —")
                    ui.Spacer(height=8)
                    ui.Label("CONNECTION STATUS")
                    self.connection = ui.Label("Backend: —")

    def apply(self, model: dict[str, Any]) -> None:
        backend = model.get("backend_status") or "OFFLINE"
        self.backend.text = f"Backend: {backend}"
        self.connection.text = f"Backend: {backend}"
        self.asset_id.text = f"Asset ID: {dash(model.get('asset_id'))}"
        self.reduction.text = f"Reduction Ratio: {model.get('reduction_ratio')}"
        self.die.text = f"Die Half Angle: {model.get('die_half_angle_rad')}"
        self.friction.text = f"Friction Coefficient: {model.get('friction_coefficient')}"
        self.hardening.text = f"Normalized Hardening Coefficient: {model.get('normalized_hardening_coefficient')}"
        self.state_version.text = f"State Version: {model.get('state_version')}"
        self.source_ts.text = f"Source Timestamp: {model.get('source_timestamp')}"
        self.source_quality.text = f"Source Quality: {model.get('source_quality')}"
        self.verdict.text = f"Latest Verdict: {model.get('latest_verdict_label')}"
        self.evaluation_id.text = f"Evaluation ID: {model.get('evaluation_id')}"
        self.snapshot_id.text = f"Snapshot ID: {model.get('snapshot_id')}"
        self.decision_id.text = f"Decision ID: {model.get('decision_id')}"
        self.routing.text = f"Routing Action: {model.get('routing_action')}"
        self.model.text = f"Model Version: {model.get('model_version')}"
        self.fea_job.text = f"FEA Job ID: {model.get('fea_job_id')}"
        self.fea_status.text = f"FEA Status: {model.get('fea_status')}"
        self.solver.text = f"Solver: {model.get('solver')}"
        self.solver_version.text = f"Solver Version: {model.get('solver_version')}"
        self.criterion.text = f"Criterion Verdict: {model.get('criterion_verdict')}"
        self.quality.text = f"Quality: {model.get('fea_quality')}"
        self.last_fea.text = f"Last Completed FEA Job ID: {model.get('last_completed_fea_job_id')}"

    def destroy(self) -> None:
        self._window = None


def create_live_panel(title: str) -> LivePanel | None:
    try:
        import omni.ui as ui
    except ImportError:
        return None
    return LivePanel(title, ui)
