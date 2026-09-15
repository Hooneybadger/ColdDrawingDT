from __future__ import annotations

from typing import Any

from cold_drawing_twin.display import ATTENTION_NONE, dash, short_id

_TEXT = 0xFFE8EAED
_MUTED = 0xFF9AA0A6
_ALARM = 0xFFB0B8FF
_WARN = 0xFFB8E6FF
_OK = 0xFF8FCF9A
_INFO = 0xFFC97E3D
_HIST = 0xFF8A9098
_VERDICT = 38


def _set_line(widget, text: str, *, filled_height: int = 18) -> None:
    widget.text = text or ""
    try:
        widget.visible = bool(widget.text)
        widget.height = filled_height if widget.text else 0
    except Exception:
        pass


class _Ghost:
    def __init__(self) -> None:
        self.text = ""
        self.visible = False
        self.style = {}
        self.height = 0


class LivePanel:
    """Compact industrial omni.ui faceplate. Display only. Sized for 1920x1080 capture."""

    def __init__(self, title: str, ui_module) -> None:
        ui = ui_module
        self._window = ui.Window(title, width=400, height=680)
        stack = getattr(ui, "VStack")
        row = getattr(ui, "HStack")
        scroll = getattr(ui, "ScrollingFrame")
        spacer = getattr(ui, "Spacer")
        zstack = getattr(ui, "ZStack", stack)
        rectangle = getattr(ui, "Rectangle", None)
        with self._window.frame:
            with zstack():
                if rectangle is not None:
                    rectangle(style={"background_color": 0xF216191D})
                with stack(spacing=3):
                        self.title = ui.Label("DRAWING 04", style={"font_size": 28, "color": _TEXT})
                        self.asset_id = ui.Label("BG.MIEUM.DRW.04", style={"font_size": 17, "color": _MUTED})
                        self.verdict = ui.Label("—", style={"font_size": _VERDICT, "color": _TEXT})
                        self.backend = ui.Label("—", style={"font_size": 18, "color": _MUTED})
                        self.banner = ui.Label("", word_wrap=True, style={"font_size": 19, "color": _MUTED})
                        self.action = self.banner
                        ui.Label("PROCESS", style={"font_size": 15, "color": _MUTED})
                        self._pv_labels = []
                        for _ in range(4):
                            with row(height=18):
                                name = ui.Label("—", width=140, style={"font_size": 16, "color": _MUTED})
                                value = ui.Label("—", width=150, style={"font_size": 18, "color": _TEXT})
                                unit = ui.Label("", width=50, style={"font_size": 15, "color": _MUTED})
                            self._pv_labels.append((name, value, unit))
                        spacer(height=2)
                        ui.Label("CURRENT EVALUATION", style={"font_size": 15, "color": _MUTED})
                        self.routing = ui.Label("Route  —", style={"font_size": 18, "color": _TEXT})
                        self.model = ui.Label("Model  —", style={"font_size": 18, "color": _TEXT})
                        self.evaluation_id = ui.Label("Evaluation  —", style={"font_size": 18, "color": _TEXT})
                        self.snapshot_id = ui.Label("Snapshot  —", style={"font_size": 18, "color": _TEXT})
                        self.eval_status = ui.Label("", height=0, style={"font_size": 18, "color": _MUTED})
                        spacer(height=2)
                        self.decision_heading = ui.Label("DECISION", style={"font_size": 15, "color": _MUTED})
                        self.decision_id = ui.Label("Decision  —", style={"font_size": 18, "color": _TEXT})
                        spacer(height=2)
                        ui.Label("FEA", style={"font_size": 15, "color": _MUTED})
                        self.fea_status = ui.Label("Status  —", style={"font_size": 20, "color": _TEXT})
                        self.fea_details = ui.Label("", word_wrap=True, height=0, style={"font_size": 18, "color": _TEXT})
                        spacer()
        self.quality_src = _Ghost()
        self.source = _Ghost()
        self.last_finalized = _Ghost()
        self.quality = _Ghost()
        self.criterion = _Ghost()
        self.fea_job = _Ghost()
        self.solver = _Ghost()
        self.solver_version = _Ghost()
        self.last_fea = _Ghost()
        self.connection = _Ghost()
        self._lineage_frame = None
        self._fea_frame = None

    def apply(self, model: dict[str, Any]) -> None:
        backend = model.get("backend_status") or "OFFLINE"
        attention = model.get("attention") or ATTENTION_NONE
        headline = dash(model.get("headline") or model.get("latest_verdict_label") or model.get("latest_verdict"))
        self.title.text = model.get("title") or "DRAWING 04"
        self.asset_id.text = dash(model.get("asset_id"))
        self.backend.text = backend
        self.verdict.text = headline
        try:
            if attention == "alarm":
                self.verdict.style = {"font_size": _VERDICT, "color": _ALARM}
            elif attention == "warning" or headline == "MANUAL REVIEW":
                self.verdict.style = {"font_size": _VERDICT, "color": _WARN}
            elif headline == "WAITING FOR FEA":
                self.verdict.style = {"font_size": _VERDICT, "color": _INFO}
            elif headline == "SAFE":
                self.verdict.style = {"font_size": _VERDICT, "color": _OK}
            else:
                self.verdict.style = {"font_size": _VERDICT, "color": _TEXT}
        except Exception:
            pass
        try:
            self.backend.style = {"font_size": 18, "color": _OK if backend == "ONLINE" else _MUTED}
        except Exception:
            pass
        if headline == "WAITING FOR FEA":
            _set_line(self.banner, "Engineering decision pending.")
        elif headline == "MANUAL REVIEW":
            _set_line(self.banner, f"Engineering verdict  {dash(model.get('engineering_verdict'))}")
        elif attention != ATTENTION_NONE:
            _set_line(self.banner, model.get("text") or "")
        else:
            _set_line(self.banner, "")
        rows = model.get("process_variables") or []
        fallback = [
            ("Reduction", model.get("reduction_ratio"), ""),
            ("Die angle", model.get("die_half_angle_rad"), "rad"),
            ("Friction", model.get("friction_coefficient"), ""),
            ("Hardening", model.get("normalized_hardening_coefficient"), ""),
        ]
        labels = ["Reduction", "Die angle", "Friction", "Hardening"]
        for index, (name, value, unit) in enumerate(self._pv_labels):
            if index < len(rows):
                item = rows[index]
                name.text = labels[index]
                value.text = dash(item.get("value"))
                unit.text = item.get("unit") or fallback[index][2]
            else:
                lab, raw, unit_text = fallback[index]
                name.text = lab
                value.text = dash(raw)
                unit.text = unit_text
        _set_line(self.quality_src, "")
        _set_line(self.source, "")
        self.routing.text = f"Route              {dash(model.get('current_route') or model.get('routing_action'))}"
        self.model.text = f"Model              {dash(model.get('model_version'))}"
        self.evaluation_id.text = f"Evaluation         {short_id(model.get('evaluation_id'))}"
        self.snapshot_id.text = f"Snapshot           {short_id(model.get('snapshot_id'))}"
        eval_status = model.get("evaluation_status") or ""
        if eval_status == "WAITING FOR FEA":
            _set_line(self.eval_status, "Status             WAITING FOR FEA")
        elif eval_status and eval_status != headline:
            _set_line(self.eval_status, eval_status)
        else:
            _set_line(self.eval_status, "")
        if model.get("show_last_finalized"):
            self.decision_heading.text = "LAST FINALIZED DECISION"
            try:
                self.decision_heading.style = {"font_size": 14, "color": _HIST}
                self.decision_id.style = {"font_size": 16, "color": _HIST}
            except Exception:
                pass
            self.decision_id.text = (
                f"{dash(model.get('last_finalized_verdict') or model.get('latest_verdict'))}  "
                f"{short_id(model.get('decision_id'))}"
            )
            _set_line(self.last_finalized, "")
        else:
            self.decision_heading.text = "DECISION"
            try:
                self.decision_heading.style = {"font_size": 15, "color": _MUTED}
                self.decision_id.style = {"font_size": 18, "color": _TEXT}
            except Exception:
                pass
            self.decision_id.text = f"Decision           {short_id(model.get('decision_id'))}"
            _set_line(self.last_finalized, "")
        headline_fea = dash(model.get("fea_headline") or model.get("fea_status"))
        if headline_fea == "NOT REQUIRED":
            self.fea_status.text = "NOT REQUIRED"
            _set_line(self.fea_job, "")
            _set_line(self.solver, "")
            _set_line(self.solver_version, "")
            _set_line(self.criterion, "")
            _set_line(self.quality, "")
        elif headline_fea == "COMPLETED":
            self.fea_status.text = "COMPLETED"
            _set_line(self.quality, f"Numerical quality  {dash(model.get('fea_quality'))}")
            _set_line(self.criterion, f"Engineering criterion  {dash(model.get('criterion_verdict'))}")
            _set_line(self.fea_job, f"Job                {short_id(model.get('current_fea_job_id') or model.get('fea_job_id'))}")
            _set_line(self.solver, "")
            _set_line(self.solver_version, "")
        else:
            self.fea_status.text = headline_fea
            _set_line(self.fea_job, f"Job                {short_id(model.get('current_fea_job_id') or model.get('fea_job_id'))}")
            solver = dash(model.get("solver"))
            _set_line(self.solver, "" if solver == "—" else f"Solver             {solver}")
            version = dash(model.get("solver_version"))
            if version in {"—", "unset"} or version.lower() == "none":
                _set_line(self.solver_version, "")
            else:
                _set_line(self.solver_version, f"Solver version     {version}")
            _set_line(self.criterion, "")
            _set_line(self.quality, "")
        history = dash(model.get("history_fea_job_id") or model.get("last_completed_fea_job_id"))
        if headline_fea == "NOT REQUIRED" or history == "—" or model.get("show_last_finalized"):
            _set_line(self.last_fea, "")
        else:
            _set_line(self.last_fea, f"History            {short_id(history)}")
        _set_line(self.connection, "")
        details = [
            self.quality.text,
            self.criterion.text,
            self.fea_job.text,
            self.solver.text,
            self.solver_version.text,
            self.last_fea.text,
        ]
        shown = [line for line in details if line]
        _set_line(self.fea_details, "\n".join(shown), filled_height=20 * max(len(shown), 0))

    def destroy(self) -> None:
        self._window = None


def create_live_panel(title: str) -> LivePanel | None:
    try:
        import omni.ui as ui
    except ImportError:
        return None
    return LivePanel(title, ui)
