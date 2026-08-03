from __future__ import annotations

try:
    from omni.ext import IExt
except ImportError:

    class IExt:  # type: ignore[no-redef]
        def on_startup(self, ext_id):
            return None

        def on_shutdown(self):
            return None


from cold_drawing_twin.display import apply_status_attributes
from omni.cold_drawing.operator.client import OperatorClient


class ColdDrawingOperatorExtension(IExt):
    def on_startup(self, ext_id):
        self.client = OperatorClient("http://127.0.0.1:8000")
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
        view = self.client.status()
        self.latest = apply_status_attributes({}, view)
        return self.latest
