from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from cold_drawing_twin.config_files import asset_registry
from cold_drawing_twin.domain.features import ProcessFeatures, features_from_mapping
from cold_drawing_twin.domain.ids import new_id
from cold_drawing_twin.domain.lineage import utc_now
from cold_drawing_twin.persistence.models import AssetStateRow, MeasurementRow
from cold_drawing_twin.twin.basyx import BasyxClient


class TwinStore:
    def __init__(self, session: Session, basyx: BasyxClient | None = None) -> None:
        self.session = session
        self.basyx = basyx or BasyxClient("", enabled=False)

    def get(self, asset_id: str) -> AssetStateRow | None:
        return self.session.get(AssetStateRow, asset_id)

    def require(self, asset_id: str) -> AssetStateRow:
        row = self.get(asset_id)
        if row is None:
            raise KeyError(asset_id)
        return row

    def features(self, asset_id: str) -> ProcessFeatures:
        row = self.require(asset_id)
        return features_from_mapping(row.features)

    def put_process_state(
        self,
        asset_id: str,
        features: ProcessFeatures,
        *,
        source_timestamp: datetime,
        quality: str = "GOOD",
        pass_index: int | None = 1,
        material_profile_id: str = "stainless_reference_v1",
        state_version: str | None = None,
        operational: bool = True,
    ) -> AssetStateRow:
        if asset_id not in asset_registry():
            raise KeyError(asset_id)
        now = utc_now()
        row = self.get(asset_id)
        version = state_version or new_id("state")
        if row is None:
            row = AssetStateRow(asset_id=asset_id, features=features.as_dict())
            self.session.add(row)
        if operational:
            row.features = features.as_dict()
            row.state_version = version
            row.pass_index = pass_index
            row.material_profile_id = material_profile_id
            row.source_timestamp = source_timestamp
            row.ingest_timestamp = now
            row.quality = quality
            for name, value in features.as_dict().items():
                self.session.add(
                    MeasurementRow(
                        asset_id=asset_id,
                        field=name,
                        value=value,
                        source_time=source_timestamp,
                        ingest_time=now,
                        quality=quality,
                    )
                )
            self.basyx.upsert_asset(asset_id, _row_dict(row))
        self.session.flush()
        return row

    def record_evaluation(
        self,
        asset_id: str,
        *,
        evaluation_id: str,
        snapshot_id: str,
        decision_id: str | None,
        verdict: str | None,
        operational: bool,
    ) -> None:
        if not operational:
            return
        row = self.require(asset_id)
        row.latest_evaluation_id = evaluation_id
        row.latest_snapshot_id = snapshot_id
        row.latest_decision_id = decision_id
        row.latest_verdict = verdict
        self.basyx.upsert_asset(asset_id, _row_dict(row))

    def record_fea_job(self, asset_id: str, job_id: str, *, active: bool, operational: bool) -> None:
        if not operational:
            return
        row = self.require(asset_id)
        if active:
            row.active_fea_job_id = job_id
        else:
            row.active_fea_job_id = None
            row.last_completed_fea_job_id = job_id
        self.basyx.upsert_asset(asset_id, _row_dict(row))


def _row_dict(row: AssetStateRow) -> dict[str, Any]:
    return {
        "state_version": row.state_version,
        "features": row.features,
        "pass_index": row.pass_index,
        "source_timestamp": row.source_timestamp,
        "quality": row.quality,
        "latest_evaluation_id": row.latest_evaluation_id,
        "latest_snapshot_id": row.latest_snapshot_id,
        "latest_decision_id": row.latest_decision_id,
        "latest_verdict": row.latest_verdict,
        "active_fea_job_id": row.active_fea_job_id,
        "last_completed_fea_job_id": row.last_completed_fea_job_id,
    }
