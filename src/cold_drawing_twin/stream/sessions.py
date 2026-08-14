from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from threading import Lock

from cold_drawing_twin.domain.ids import new_id
from cold_drawing_twin.domain.lineage import utc_now
from cold_drawing_twin.observability.gpu import GpuSample

STREAM_SESSION_TTL_S = 45
STREAM_ROLES = frozenset({"operator", "senior"})
STREAM_CLIENTS = frozenset({"kit", "browser"})


@dataclass
class StreamSession:
    session_id: str
    role: str
    client: str
    asset_id: str
    created_at: datetime
    last_heartbeat: datetime
    gpu: GpuSample | None = None


class StreamSessionStore:
    def __init__(self, ttl_s: int = STREAM_SESSION_TTL_S) -> None:
        self.ttl_s = ttl_s
        self._lock = Lock()
        self._sessions: dict[str, StreamSession] = {}

    def create(self, *, role: str, client: str, asset_id: str) -> StreamSession:
        if role not in STREAM_ROLES:
            raise ValueError("role must be operator or senior")
        if client not in STREAM_CLIENTS:
            raise ValueError("client must be kit or browser")
        if not asset_id:
            raise ValueError("asset_id is required")
        now = utc_now()
        session = StreamSession(
            session_id=new_id("stream"),
            role=role,
            client=client,
            asset_id=asset_id,
            created_at=now,
            last_heartbeat=now,
        )
        with self._lock:
            self._sessions[session.session_id] = session
        return session

    def get(self, session_id: str, *, now: datetime | None = None) -> StreamSession | None:
        stamp = now or utc_now()
        with self._lock:
            return self._alive(session_id, stamp)

    def heartbeat(
        self,
        session_id: str,
        gpu: GpuSample | None = None,
        *,
        now: datetime | None = None,
    ) -> StreamSession | None:
        stamp = now or utc_now()
        with self._lock:
            session = self._alive(session_id, stamp)
            if session is None:
                return None
            session.last_heartbeat = stamp
            if gpu is not None:
                session.gpu = gpu
            return session

    def end(self, session_id: str) -> bool:
        with self._lock:
            return self._sessions.pop(session_id, None) is not None

    def active(self, *, now: datetime | None = None) -> list[StreamSession]:
        stamp = now or utc_now()
        with self._lock:
            expired = [sid for sid, session in self._sessions.items() if self._expired(session, stamp)]
            for sid in expired:
                del self._sessions[sid]
            return list(self._sessions.values())

    def clear(self) -> None:
        with self._lock:
            self._sessions.clear()

    def _alive(self, session_id: str, now: datetime) -> StreamSession | None:
        session = self._sessions.get(session_id)
        if session is None:
            return None
        if self._expired(session, now):
            del self._sessions[session_id]
            return None
        return session

    def _expired(self, session: StreamSession, now: datetime) -> bool:
        return (now - session.last_heartbeat).total_seconds() > self.ttl_s


STREAM_STORE = StreamSessionStore()
