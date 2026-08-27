from __future__ import annotations

import logging

from cold_drawing_twin.config_files import asset_registry
from cold_drawing_twin.display import panel_model
from cold_drawing_twin.kit_panel import create_live_panel
from cold_drawing_twin.usd_status import apply_status_to_stage, current_kit_stage

LOGGER = logging.getLogger(__name__)


class LiveViewController:
    """Poll the backend live view, update omni.ui, and bind Drawing 4 USD."""

    def __init__(self, client, asset_id: str, title: str) -> None:
        self.client = client
        self.asset_id = asset_id
        self.panel = create_live_panel(title)
        self.latest = None
        self._logged_offline = False

    def _load_live(self) -> dict:
        if hasattr(self.client, "fetch_live"):
            return self.client.fetch_live()
        return self.client.live(self.asset_id)

    def tick(self) -> dict:
        usd_prim = asset_registry().get(self.asset_id, {}).get("usd_prim") or ""
        try:
            live = self._load_live()
            model = panel_model(live, backend_online=True)
            if self._logged_offline:
                LOGGER.info("backend reachable again")
            self._logged_offline = False
        except Exception:
            if not self._logged_offline:
                LOGGER.warning("backend unreachable; operator display is OFFLINE")
                self._logged_offline = True
            model = panel_model(
                {"asset_id": self.asset_id, "usd_prim": usd_prim},
                backend_online=False,
            )
        if not model.get("usd_prim"):
            model["usd_prim"] = usd_prim
        if self.panel is not None:
            try:
                self.panel.apply(model)
            except Exception:
                LOGGER.debug("omni.ui panel update failed", exc_info=False)
        try:
            apply_status_to_stage(current_kit_stage(), model.get("usd_prim") or usd_prim, model)
        except Exception:
            LOGGER.debug("USD status bind failed", exc_info=False)
        self.latest = model
        return model

    def shutdown(self) -> None:
        if self.panel is not None:
            self.panel.destroy()
        self.panel = None
