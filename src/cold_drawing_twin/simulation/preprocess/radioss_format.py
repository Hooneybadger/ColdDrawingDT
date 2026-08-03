from __future__ import annotations

from collections.abc import Iterable, Sequence


def i10(*values: int | None) -> str:
    parts: list[str] = []
    for value in values:
        parts.append(" " * 10 if value is None else f"{value:10d}")
    return "".join(parts)


def e20(*values: float | None) -> str:
    parts: list[str] = []
    for value in values:
        if value is None:
            parts.append(" " * 20)
        else:
            parts.append(f"{value:20.12E}")
    return "".join(parts)


def trarot(tx: int, ty: int, tz: int, rx: int = 0, ry: int = 0, rz: int = 0) -> str:
    """Radioss Trarot: 10 characters, codes right-justified as TX TY TZ _ RX RY RZ."""
    return f"   {tx}{ty}{tz} {rx}{ry}{rz}"


def chunked(values: Sequence[int], size: int = 10) -> Iterable[list[int]]:
    for index in range(0, len(values), size):
        yield list(values[index : index + size])
