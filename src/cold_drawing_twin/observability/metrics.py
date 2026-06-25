from __future__ import annotations

from prometheus_client import Counter, Histogram
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
decisions_total = Counter("decisions_total", "Decisions", ["verdict"])
manual_review_total = Counter("manual_review_total", "Manual review", ["reason"])
twin_updates_total = Counter("twin_updates_total", "Twin updates", ["asset_id", "status"])
http_requests_total = Counter("http_requests_total", "HTTP requests", ["path", "method", "status"])


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        http_requests_total.labels(request.url.path, request.method, str(response.status_code)).inc()
        return response


def install_metrics(app) -> None:
    app.add_middleware(MetricsMiddleware)
