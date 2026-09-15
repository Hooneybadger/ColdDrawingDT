from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from cold_drawing_twin.api.routes import get_session
from cold_drawing_twin.config_files import asset_registry
from cold_drawing_twin.display import attach_current_analysis
from cold_drawing_twin.twin.basyx import BasyxClient, read_projected_view

router = APIRouter()
INSPECTOR_HTML = Path(__file__).resolve().parents[1] / "web" / "aas_inspector.html"


def _basyx_client() -> BasyxClient:
    from cold_drawing_twin.api.app import container

    settings = container.settings
    return BasyxClient(settings.basyx_aas_repository_url, enabled=settings.basyx_enabled)


@router.get("/aas-inspector")
def aas_inspector_page():
    if not INSPECTOR_HTML.is_file():
        raise HTTPException(500, "AAS inspector page is missing")
    return FileResponse(INSPECTOR_HTML, media_type="text/html")


@router.get("/aas/{asset_id}/view")
def get_aas_view(asset_id: str, session: Session = Depends(get_session)):
    if asset_id not in asset_registry():
        raise HTTPException(404, "unknown asset")
    view = read_projected_view(_basyx_client(), asset_id)
    live = None
    if (view.get("simulation") or {}).get("activeFeaJobId"):
        from cold_drawing_twin.api.live import live_view

        live = live_view(session, asset_id)
    return attach_current_analysis(view, live)
