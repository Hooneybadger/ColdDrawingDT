from __future__ import annotations

from sqlalchemy.orm import Session

from cold_drawing_twin.domain.ids import new_id
from cold_drawing_twin.domain.lineage import utc_now
from cold_drawing_twin.persistence.models import FeaOutboxRow


def unpublished_outbox_job_ids(session: Session) -> list[str]:
    rows = (
        session.query(FeaOutboxRow)
        .filter(FeaOutboxRow.published_at.is_(None))
        .order_by(FeaOutboxRow.created_at.asc())
        .all()
    )
    seen: list[str] = []
    for row in rows:
        if row.job_id not in seen:
            seen.append(row.job_id)
    return seen


def ensure_unpublished_outbox(session: Session, job_id: str) -> FeaOutboxRow:
    unpublished = (
        session.query(FeaOutboxRow)
        .filter(FeaOutboxRow.job_id == job_id, FeaOutboxRow.published_at.is_(None))
        .first()
    )
    if unpublished is not None:
        return unpublished
    tracked = session.query(FeaOutboxRow).filter(FeaOutboxRow.job_id == job_id).first()
    if tracked is not None:
        return tracked
    row = FeaOutboxRow(
        outbox_id=new_id("outbox"),
        job_id=job_id,
        created_at=utc_now(),
        published_at=None,
        last_error=None,
    )
    session.add(row)
    session.flush()
    return row


def mark_outbox_published(session: Session, job_id: str) -> None:
    now = utc_now()
    rows = (
        session.query(FeaOutboxRow)
        .filter(FeaOutboxRow.job_id == job_id, FeaOutboxRow.published_at.is_(None))
        .all()
    )
    for row in rows:
        row.published_at = now
        row.last_error = None


def record_outbox_error(session: Session, job_id: str, message: str) -> None:
    rows = (
        session.query(FeaOutboxRow)
        .filter(FeaOutboxRow.job_id == job_id, FeaOutboxRow.published_at.is_(None))
        .all()
    )
    for row in rows:
        row.last_error = message[:2000]
