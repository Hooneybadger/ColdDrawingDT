from __future__ import annotations

from datetime import timezone

from prometheus_client import Counter, Gauge, Histogram
from sqlalchemy.orm import Session
from starlette.middleware.base import BaseHTTPMiddleware

pinn_inference_duration_seconds = Histogram(
    "pinn_inference_duration_seconds",
    "PINN inference duration",
)
pinn_results_total = Counter(
    "pinn_results_total",
    "PINN results",
    ["verdict", "model_version"],
)
pinn_failures_total = Counter("pinn_failures_total", "PINN failures", ["reason"])
fea_jobs_total = Counter("fea_jobs_total", "FEA jobs", ["status"])
fea_job_duration_seconds = Histogram(
    "fea_job_duration_seconds",
    "FEA job wall time including preprocess and solver",
)
decisions_total = Counter("decisions_total", "Decisions", ["verdict"])
manual_review_total = Counter("manual_review_total", "Manual review", ["reason"])
twin_updates_total = Counter("twin_updates_total", "Twin updates", ["asset_id", "status"])
evaluations_blocked_total = Counter(
    "evaluations_blocked_total",
    "Evaluations blocked before an automatic Decision",
    ["reason"],
)
http_requests_total = Counter("http_requests_total", "HTTP requests", ["path", "method", "status"])
twin_state_age_seconds = Gauge(
    "twin_state_age_seconds",
    "Age of Twin source_timestamp at scrape time",
    ["asset_id"],
)
fea_queue_depth = Gauge("fea_queue_depth", "FEA jobs in QUEUED")
fea_running_jobs = Gauge("fea_running_jobs", "FEA jobs in RUNNING")


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        http_requests_total.labels(request.url.path, request.method, str(response.status_code)).inc()
        return response


def scrape_runtime_gauges(session: Session) -> None:
    """Set gauges from the database at scrape time. Does not invent values."""
    from cold_drawing_twin.domain.lineage import utc_now
    from cold_drawing_twin.domain.types import FeaJobStatus
    from cold_drawing_twin.persistence.models import AssetStateRow, FeaJobRow

    now = utc_now()
    for row in session.query(AssetStateRow).all():
        source = row.source_timestamp
        if source is None:
            continue
        if source.tzinfo is None:
            source = source.replace(tzinfo=timezone.utc)
        twin_state_age_seconds.labels(row.asset_id).set((now - source).total_seconds())
    fea_queue_depth.set(
        session.query(FeaJobRow).filter(FeaJobRow.status == FeaJobStatus.QUEUED.value).count()
    )
    fea_running_jobs.set(
        session.query(FeaJobRow).filter(FeaJobRow.status == FeaJobStatus.RUNNING.value).count()
    )


def install_metrics(app) -> None:
    app.add_middleware(MetricsMiddleware)
