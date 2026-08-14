from __future__ import annotations

from fastapi import APIRouter, HTTPException

from cold_drawing_twin.api.schemas import StreamHeartbeat, StreamSessionCreate
from cold_drawing_twin.observability.gpu import GpuSample
from cold_drawing_twin.stream.sessions import STREAM_STORE, StreamSession

router = APIRouter()


def _gpu_body(sample: GpuSample | None) -> dict | None:
    if sample is None:
        return None
    return {
        "index": sample.index,
        "utilization_ratio": sample.utilization_ratio,
        "memory_used_bytes": sample.memory_used_bytes,
        "memory_total_bytes": sample.memory_total_bytes,
    }


def session_body(session: StreamSession) -> dict:
    return {
        "session_id": session.session_id,
        "role": session.role,
        "client": session.client,
        "asset_id": session.asset_id,
        "created_at": session.created_at.isoformat(),
        "last_heartbeat": session.last_heartbeat.isoformat(),
        "gpu": _gpu_body(session.gpu),
        "display_only": True,
    }


@router.post("/stream/sessions")
def create_stream_session(body: StreamSessionCreate):
    try:
        session = STREAM_STORE.create(role=body.role, client=body.client, asset_id=body.asset_id)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return session_body(session)


@router.get("/stream/sessions")
def list_stream_sessions():
    return {"sessions": [session_body(item) for item in STREAM_STORE.active()]}


@router.get("/stream/sessions/{session_id}")
def get_stream_session(session_id: str):
    session = STREAM_STORE.get(session_id)
    if session is None:
        raise HTTPException(404, "stream session not found")
    return session_body(session)


@router.post("/stream/sessions/{session_id}/heartbeat")
def heartbeat_stream_session(session_id: str, body: StreamHeartbeat | None = None):
    gpu = None
    if body is not None and body.gpu is not None:
        gpu = GpuSample(
            index=body.gpu.index,
            utilization_ratio=body.gpu.utilization_ratio,
            memory_used_bytes=body.gpu.memory_used_bytes,
            memory_total_bytes=body.gpu.memory_total_bytes,
        )
    session = STREAM_STORE.heartbeat(session_id, gpu)
    if session is None:
        raise HTTPException(404, "stream session not found")
    return session_body(session)


@router.delete("/stream/sessions/{session_id}")
def end_stream_session(session_id: str):
    if not STREAM_STORE.end(session_id):
        raise HTTPException(404, "stream session not found")
    return {"ended": True}
