from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from cold_drawing_twin.config_files import asset_registry
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
def get_aas_view(asset_id: str):
    if asset_id not in asset_registry():
        raise HTTPException(404, "unknown asset")
    return read_projected_view(_basyx_client(), asset_id)
