from __future__ import annotations

from datetime import datetime, timezone

import pytest

from cold_drawing_twin.domain.features import ProcessFeatures
from cold_drawing_twin.domain.routing import PinnResult
from cold_drawing_twin.inference.pinn.adapter import StaticPinnAdapter
from cold_drawing_twin.orchestration.container import build_container
from cold_drawing_twin.settings import Settings

DEMO = ProcessFeatures(0.3, 0.2, 0.08, 0.7)
PRIMARY = "BG.MIEUM.DRW.04"


def make_pinn(verdict: str, supported: bool = True) -> StaticPinnAdapter:
    return StaticPinnAdapter(
        PinnResult(verdict, 0.1, 0.0, 0.01, None, "v0.1.1", supported, {"decision": verdict})
    )


@pytest.fixture
def settings(tmp_path):
    return Settings(
        database_url=f"sqlite:///{tmp_path / 'test.db'}",
        fea_execution="inline",
        basyx_enabled=False,
        openradioss_work_dir=tmp_path / "fea",
        openradioss_starter_bin="",
        openradioss_engine_bin="",
        pinn_model_dir=tmp_path / "missing-pinn",
        _env_file=None,
    )


@pytest.fixture
def seeded(settings):
    container = build_container(settings=settings, pinn=make_pinn("SAFE"))
    session = container.open()
    twin, events, evaluation = container.services(session)
    twin.put_process_state(
        PRIMARY,
        DEMO,
        source_timestamp=datetime.now(timezone.utc),
        quality="GOOD",
        state_version="state-0001",
    )
    session.commit()
    return container, session, twin, events, evaluation
