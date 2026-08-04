from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Float, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker


class Base(DeclarativeBase):
    pass


class AssetStateRow(Base):
    __tablename__ = "asset_state"

    asset_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    state_version: Mapped[str] = mapped_column(String(64))
    pass_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    features: Mapped[dict[str, Any]] = mapped_column(JSON)
    material_profile_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    source_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ingest_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    quality: Mapped[str] = mapped_column(String(32), default="GOOD")
    latest_evaluation_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    latest_snapshot_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    latest_decision_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    latest_verdict: Mapped[str | None] = mapped_column(String(32), nullable=True)
    active_fea_job_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_completed_fea_job_id: Mapped[str | None] = mapped_column(String(64), nullable=True)


class MeasurementRow(Base):
    __tablename__ = "measurements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    asset_id: Mapped[str] = mapped_column(String(64), index=True)
    field: Mapped[str] = mapped_column(String(64), index=True)
    value: Mapped[float] = mapped_column(Float)
    source_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    ingest_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    quality: Mapped[str] = mapped_column(String(32))


class SnapshotRow(Base):
    __tablename__ = "snapshots"

    snapshot_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    asset_id: Mapped[str] = mapped_column(String(64), index=True)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    source_state_version: Mapped[str] = mapped_column(String(64))
    features: Mapped[dict[str, Any]] = mapped_column(JSON)
    mode: Mapped[str] = mapped_column(String(32))


class EvaluationRow(Base):
    __tablename__ = "evaluations"

    evaluation_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    asset_id: Mapped[str] = mapped_column(String(64), index=True)
    snapshot_id: Mapped[str] = mapped_column(String(64), index=True)
    scenario_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    mode: Mapped[str] = mapped_column(String(32))
    state: Mapped[str] = mapped_column(String(32), index=True)
    routing_action: Mapped[str | None] = mapped_column(String(32), nullable=True)
    pinn_result: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ScenarioRow(Base):
    __tablename__ = "scenarios"

    scenario_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    base_snapshot_id: Mapped[str] = mapped_column(String(64))
    evaluation_id: Mapped[str] = mapped_column(String(64), index=True)
    overrides: Mapped[dict[str, Any]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class FeaJobRow(Base):
    __tablename__ = "fea_jobs"

    job_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    evaluation_id: Mapped[str] = mapped_column(String(64), index=True)
    snapshot_id: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    solver: Mapped[str] = mapped_column(String(32), default="OpenRadioss")
    solver_version: Mapped[str] = mapped_column(String(64), default="unset")
    material_mapping_version: Mapped[str] = mapped_column(String(64))
    mesh_config_version: Mapped[str] = mapped_column(String(64))
    fea_profile_version: Mapped[str] = mapped_column(String(64))
    safety_criterion_version: Mapped[str] = mapped_column(String(64))
    idempotency_key: Mapped[str] = mapped_column(String(64), index=True)
    work_dir: Mapped[str | None] = mapped_column(Text, nullable=True)
    quality: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    metrics: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    artifacts: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    criterion_verdict: Mapped[str | None] = mapped_column(String(32), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class DecisionRow(Base):
    __tablename__ = "decisions"

    decision_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    evaluation_id: Mapped[str] = mapped_column(String(64), index=True)
    snapshot_id: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(32))
    verdict: Mapped[str] = mapped_column(String(32))
    model_version: Mapped[str] = mapped_column(String(64))
    routing_policy_version: Mapped[str] = mapped_column(String(64))
    fea_job_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    lineage: Mapped[dict[str, Any]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class EventRow(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


def make_engine(url: str):
    if url.startswith("sqlite:///"):
        from pathlib import Path

        Path(url.removeprefix("sqlite:///")).parent.mkdir(parents=True, exist_ok=True)
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    engine = create_engine(url, future=True, connect_args=connect_args)
    return engine


def make_session_factory(url: str):
    engine = make_engine(url)
    Base.metadata.create_all(engine)
    if url.startswith("postgresql"):
        with engine.begin() as conn:
            conn.exec_driver_sql("CREATE EXTENSION IF NOT EXISTS timescaledb")
            try:
                conn.exec_driver_sql(
                    "SELECT create_hypertable('measurements', 'source_time', if_not_exists => TRUE)"
                )
            except Exception:
                pass
    return sessionmaker(bind=engine, expire_on_commit=False, future=True)
