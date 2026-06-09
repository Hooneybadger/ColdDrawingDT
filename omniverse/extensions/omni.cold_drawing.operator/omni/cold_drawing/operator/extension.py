from __future__ import annotations

try:
    from omni.ext import IExt
except ImportError:

    class IExt:  # type: ignore[no-redef]
        def on_startup(self, ext_id):
            return None

        def on_shutdown(self):
            return None


from omni.cold_drawing.operator.client import OperatorClient


class ColdDrawingOperatorExtension(IExt):
    def on_startup(self, ext_id):
        self.client = OperatorClient("http://127.0.0.1:8000")
