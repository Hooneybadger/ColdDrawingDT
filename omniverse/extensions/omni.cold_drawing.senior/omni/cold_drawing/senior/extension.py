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

    def live_state(self):
        return self.client.asset_state(self.asset_id)

    def run_fast_evaluation(self):
        return self.client.evaluate(self.asset_id)
