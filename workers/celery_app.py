from celery import Celery

from cold_drawing_twin.domain.timeouts import fea_task_hard_limit_s, fea_task_soft_limit_s
from cold_drawing_twin.settings import load_settings

settings = load_settings()
app = Celery(
    "cold_drawing_fea",
    broker=settings.celery_broker_url or "memory://",
    backend=settings.celery_result_backend,
    include=["workers.fea_tasks"],
)
app.conf.update(
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_reject_on_worker_lost=True,
    task_default_queue="fea.default",
    task_time_limit=fea_task_hard_limit_s(settings),
    task_soft_time_limit=fea_task_soft_limit_s(settings),
    task_queues={
        "fea.default": {},
        "fea.priority": {},
    },
)
