from __future__ import annotations

try:
    from omni.ext import IExt
except ImportError:  # Kit is not present in unit tests.

    class IExt:  # type: ignore[no-redef]
        def on_startup(self, ext_id):
            return None

        def on_shutdown(self):
            return None


from omni.cold_drawing.senior.client import TwinApiClient


class ColdDrawingSeniorExtension(IExt):
    def on_startup(self, ext_id):
        self.client = TwinApiClient("http://127.0.0.1:8000")
        self.asset_id = "BG.MIEUM.DRW.04"
        self._elapsed = 0.0
        self.latest = None
        self._sub = None
        try:
            import omni.kit.app

            self._sub = omni.kit.app.get_app().get_update_event_stream().create_subscription_to_pop(self._on_update)
        except Exception:
            self._sub = None

    def on_shutdown(self):
        self._sub = None

    def _on_update(self, event):
        dt = 0.0
        if event is not None:
            dt = float(getattr(event, "payload", {}).get("dt", 0.0) or 0.0)
        self.poll(dt)

    def poll(self, dt: float = 0.0):
        self._elapsed += dt
        if self._elapsed < self.client.poll_s and self.latest is not None:
            return self.latest
        self._elapsed = 0.0
        self.latest = self.live_state()
        return self.latest

    def live_state(self):
        state = self.client.asset_state(self.asset_id)
        overview = self.client.assets()
        return {
            "factory": overview,
            "selected_asset": state,
            "fea_job": None
            if not state.get("active_fea_job_id") and not state.get("last_completed_fea_job_id")
            else self.client.fea_job(state.get("active_fea_job_id") or state.get("last_completed_fea_job_id")),
            "history_path": f"/assets/{self.asset_id}/history",
        }

    def run_fast_evaluation(self):
        return self.client.evaluate(self.asset_id)
