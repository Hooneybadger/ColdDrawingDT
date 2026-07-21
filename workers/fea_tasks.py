from __future__ import annotations

from workers.celery_app import app


def enqueue_fea_job(job_id: str, priority: bool = False) -> None:
    queue = "fea.priority" if priority else "fea.default"
    run_fea_job_task.apply_async(args=[job_id], queue=queue)


@app.task(acks_late=True, name="workers.fea_tasks.run_fea_job")
def run_fea_job_task(job_id: str) -> str:
    from cold_drawing_twin.orchestration.container import build_container
    from cold_drawing_twin.orchestration.fea import run_fea_job

    container = build_container()
    session = container.open()
    try:
        twin, events, _evaluation = container.services(session)
        job = run_fea_job(session, job_id, container.settings, events, twin)
        session.commit()
        return job.status
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
