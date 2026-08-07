from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine, inspect, text

from cold_drawing_twin.domain.lineage import SOURCE_TIMESTAMP_MEASUREMENT, SOURCE_TIMESTAMP_UNKNOWN, iso
from cold_drawing_twin.orchestration.container import build_container
from cold_drawing_twin.persistence.models import SnapshotRow, make_session_factory
from cold_drawing_twin.settings import Settings
from tests.conftest import DEMO, PRIMARY, make_pinn


def test_legacy_snapshot_source_time_stays_unknown(tmp_path):
    db = tmp_path / "legacy.db"
    url = f"sqlite:///{db}"
    engine = create_engine(url, future=True)
    captured = datetime(2026, 7, 1, 12, 0, tzinfo=timezone.utc)
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE snapshots (
                    snapshot_id VARCHAR(64) PRIMARY KEY,
                    asset_id VARCHAR(64),
                    captured_at TIMESTAMP,
                    source_state_version VARCHAR(64),
                    features JSON,
                    mode VARCHAR(32)
                )
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO snapshots
                (snapshot_id, asset_id, captured_at, source_state_version, features, mode)
                VALUES
                (:sid, :aid, :captured, :ver, :features, :mode)
                """
            ),
            {
                "sid": "snap-legacy",
                "aid": PRIMARY,
                "captured": captured,
                "ver": "state-old",
                "features": "{}",
                "mode": "OPERATIONAL",
            },
        )

    make_session_factory(url)
    columns = {column["name"] for column in inspect(engine).get_columns("snapshots")}
    assert "source_timestamp" in columns
    assert "ingest_timestamp" in columns
    assert "source_timestamp_provenance" in columns

    with engine.connect() as conn:
        row = conn.execute(
            text(
                "SELECT source_timestamp, ingest_timestamp, source_timestamp_provenance, captured_at "
                "FROM snapshots WHERE snapshot_id = :sid"
            ),
            {"sid": "snap-legacy"},
        ).one()
    assert row[0] is None
    assert row[1] is None
    assert row[2] == SOURCE_TIMESTAMP_UNKNOWN
    assert row[3] is not None

    settings = Settings(
        database_url=url,
        fea_execution="inline",
        basyx_enabled=False,
        openradioss_work_dir=tmp_path / "fea",
        openradioss_starter_bin="",
        openradioss_engine_bin="",
        pinn_model_dir=tmp_path / "missing-pinn",
        _env_file=None,
    )
    container = build_container(settings=settings, pinn=make_pinn("SAFE"))
    session = container.open()
    twin, _events, evaluation = container.services(session)
    source = datetime.now(timezone.utc) - timedelta(seconds=5)
    twin.put_process_state(PRIMARY, DEMO, source_timestamp=source, quality="GOOD")
    created = evaluation.start_operational(PRIMARY)
    fresh = session.get(SnapshotRow, created.snapshot_id)
    legacy = session.get(SnapshotRow, "snap-legacy")
    assert fresh is not None
    assert fresh.source_timestamp_provenance == SOURCE_TIMESTAMP_MEASUREMENT
    assert iso(fresh.source_timestamp) == iso(source)
    assert iso(fresh.captured_at) != iso(fresh.source_timestamp)
    assert legacy is not None
    assert legacy.source_timestamp is None
    assert legacy.source_timestamp_provenance == SOURCE_TIMESTAMP_UNKNOWN
    assert iso(legacy.source_timestamp) is None
