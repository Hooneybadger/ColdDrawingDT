from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from starlette.responses import Response

from cold_drawing_twin.api.routes import router
from cold_drawing_twin.api.stream_routes import router as stream_router
from cold_drawing_twin.observability.metrics import install_metrics, scrape_runtime_gauges
from cold_drawing_twin.orchestration.container import AppContainer, build_container

container: AppContainer


def create_app(app_container: AppContainer | None = None) -> FastAPI:
    global container
    container = app_container or build_container()
    app = FastAPI(title="Cold Drawing Digital Twin", version="1.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    install_metrics(app)
    app.include_router(router)
    app.include_router(stream_router)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/metrics")
    def metrics():
        session = container.open()
        try:
            scrape_runtime_gauges(session)
        finally:
            session.close()
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    return app
