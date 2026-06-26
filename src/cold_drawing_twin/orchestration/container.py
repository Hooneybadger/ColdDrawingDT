from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session, sessionmaker

from cold_drawing_twin.inference.pinn.adapter import PinnAdapter, ReleasedPinnAdapter
from cold_drawing_twin.orchestration.events import EventBus
from cold_drawing_twin.orchestration.evaluation import EvaluationService
from cold_drawing_twin.persistence.models import make_session_factory
from cold_drawing_twin.settings import Settings, load_settings
from cold_drawing_twin.twin.basyx import BasyxClient
from cold_drawing_twin.twin.store import TwinStore


@dataclass
class AppContainer:
    settings: Settings
    sessions: sessionmaker
    pinn: PinnAdapter

    def open(self) -> Session:
        return self.sessions()

    def services(self, session: Session) -> tuple[TwinStore, EventBus, EvaluationService]:
        twin = TwinStore(
            session,
            BasyxClient(self.settings.basyx_aas_repository_url, enabled=self.settings.basyx_enabled),
        )
        events = EventBus(session)
        enqueue = None
        if self.settings.fea_execution == "celery":
            from workers.fea_tasks import enqueue_fea_job

            enqueue = enqueue_fea_job
        else:
            from cold_drawing_twin.orchestration.fea import run_fea_job

            def enqueue(job_id: str, _session=session, _twin=twin, _events=events) -> None:
                run_fea_job(_session, job_id, self.settings, _events, _twin)

        evaluation = EvaluationService(session, twin, self.pinn, events, enqueue_fea=enqueue)
        return twin, events, evaluation


def build_container(settings: Settings | None = None, pinn: PinnAdapter | None = None) -> AppContainer:
    settings = settings or load_settings()
    sessions = make_session_factory(settings.database_url)
    adapter = pinn or ReleasedPinnAdapter(settings.pinn_model_dir, settings.pinn_model_version)
    return AppContainer(settings=settings, sessions=sessions, pinn=adapter)
