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
gpu_devices = Gauge("gpu_devices", "NVIDIA GPUs reported on scrape")
gpu_utilization_ratio = Gauge("gpu_utilization_ratio", "GPU utilization from 0 to 1", ["gpu"])
gpu_memory_used_bytes = Gauge("gpu_memory_used_bytes", "GPU memory used", ["gpu"])
gpu_memory_total_bytes = Gauge("gpu_memory_total_bytes", "GPU memory total", ["gpu"])
stream_sessions = Gauge("stream_sessions", "Active stream sessions", ["role", "client"])


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        http_requests_total.labels(_http_route_label(request), request.method, str(response.status_code)).inc()
        return response


def _http_route_label(request) -> str:
    """Use the FastAPI route template so IDs do not explode Prometheus cardinality."""
    route = request.scope.get("route")
    template = getattr(route, "path", None)
    if isinstance(template, str) and template:
        return template
    return request.url.path


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
    _scrape_stream_and_gpu()


def _scrape_stream_and_gpu() -> None:
    from collections import Counter

    from cold_drawing_twin.observability.gpu import GpuSample, read_nvidia_smi
    from cold_drawing_twin.stream.sessions import STREAM_CLIENTS, STREAM_ROLES, STREAM_STORE

    live = STREAM_STORE.active()
    counts = Counter((item.role, item.client) for item in live)
    for role in STREAM_ROLES:
        for client in STREAM_CLIENTS:
            stream_sessions.labels(role, client).set(counts.get((role, client), 0))
    samples = [item.gpu for item in live if item.gpu is not None]
    if not samples:
        samples = read_nvidia_smi()
    seen: dict[str, GpuSample] = {}
    for sample in samples:
        seen[sample.index] = sample
    gpu_devices.set(len(seen))
    for index, sample in seen.items():
        gpu_utilization_ratio.labels(index).set(sample.utilization_ratio)
        gpu_memory_used_bytes.labels(index).set(sample.memory_used_bytes)
        gpu_memory_total_bytes.labels(index).set(sample.memory_total_bytes)


def install_metrics(app) -> None:
    app.add_middleware(MetricsMiddleware)
