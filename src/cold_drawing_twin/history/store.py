from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from cold_drawing_twin.persistence.models import MeasurementRow


def history_for(session: Session, asset_id: str, limit: int = 200) -> list[dict]:
    rows = (
        session.query(MeasurementRow)
        .filter(MeasurementRow.asset_id == asset_id)
        .order_by(MeasurementRow.source_time.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "asset_id": row.asset_id,
            "field": row.field,
            "value": row.value,
            "source_time": row.source_time.isoformat() if isinstance(row.source_time, datetime) else row.source_time,
            "ingest_time": row.ingest_time.isoformat() if isinstance(row.ingest_time, datetime) else row.ingest_time,
            "quality": row.quality,
        }
        for row in rows
    ]
