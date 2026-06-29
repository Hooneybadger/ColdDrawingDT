from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

from sqlalchemy.orm import Session

from cold_drawing_twin.domain.lineage import utc_now
from cold_drawing_twin.persistence.models import EventRow

Listener = Callable[[str, dict], None]


class EventBus:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.listeners: list[Listener] = []

    def emit(self, name: str, payload: dict, when: datetime | None = None) -> None:
        row = EventRow(name=name, payload=payload, created_at=when or utc_now())
        self.session.add(row)
        self.session.flush()
        for listener in self.listeners:
            listener(name, payload)
