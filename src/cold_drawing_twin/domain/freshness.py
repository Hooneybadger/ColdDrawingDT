from __future__ import annotations

from datetime import datetime, timezone

from cold_drawing_twin.config_files import freshness_policy
from cold_drawing_twin.domain.features import FEATURE_ORDER, ProcessFeatures


def is_stale(source_timestamp: datetime, now: datetime | None = None, max_age_s: int | None = None) -> bool:
    current = now or datetime.now(timezone.utc)
    if source_timestamp.tzinfo is None:
        source_timestamp = source_timestamp.replace(tzinfo=timezone.utc)
    age = (current - source_timestamp).total_seconds()
    limit = max_age_s
    if limit is None:
        limit = int(freshness_policy()["max_age_seconds"]["process_state"])
    return age > limit


def missing_required(features: ProcessFeatures | None) -> bool:
    if features is None:
        return True
    mapping = features.as_dict()
    return any(mapping.get(name) is None for name in FEATURE_ORDER)
