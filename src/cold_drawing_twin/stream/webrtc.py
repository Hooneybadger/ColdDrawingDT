from __future__ import annotations

import asyncio
import json
from collections.abc import Callable

from aiortc import RTCPeerConnection, RTCSessionDescription

_pcs: set[RTCPeerConnection] = set()


async def answer_operator_offer(
    *,
    sdp: str,
    type_: str,
    view_factory: Callable[[], dict],
    interval_s: float = 2.0,
) -> dict[str, str]:
    """Answer a browser offer and push operator_view JSON on the data channel."""
    pc = RTCPeerConnection()
    _pcs.add(pc)

    @pc.on("connectionstatechange")
    async def on_state() -> None:
        if pc.connectionState in {"failed", "closed", "disconnected"}:
            await pc.close()
            _pcs.discard(pc)

    @pc.on("datachannel")
    def on_datachannel(channel) -> None:
        async def pump() -> None:
            while channel.readyState == "open":
                try:
                    channel.send(json.dumps(view_factory()))
                except Exception:
                    break
                await asyncio.sleep(interval_s)

        @channel.on("open")
        def on_open() -> None:
            asyncio.ensure_future(pump())

        if channel.readyState == "open":
            asyncio.ensure_future(pump())

    await pc.setRemoteDescription(RTCSessionDescription(sdp=sdp, type=type_))
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)
    return {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}


async def close_peers() -> None:
    peers = list(_pcs)
    _pcs.clear()
    for pc in peers:
        await pc.close()
