"""Centralized slow-request thresholds (ms) for observability."""

from __future__ import annotations

# operation_type from analytics middleware / view telemetry
_SLOW_MS_BY_OPERATION: dict[str, int] = {
    "database_creation": 3000,
    "database_deletion": 2000,
    "database_listing": 1000,
    "collection_creation": 2000,
    "collection_deletion": 1500,
    "collection_listing": 1000,
    "document_creation": 1000,
    "document_update": 1000,
    "document_deletion": 800,
    "document_query": 500,
    "bulk_insert": 5000,
    "single_insert": 800,
    "data_import": 10000,
    "metadata_retrieval": 500,
    "read": 500,
    "write": 1000,
    "unknown": 1000,
    "other": 1000,
}

DEFAULT_SLOW_MS = 1000


def get_slow_threshold_ms(operation_type: str) -> int:
    if not operation_type:
        return DEFAULT_SLOW_MS
    return _SLOW_MS_BY_OPERATION.get(operation_type, DEFAULT_SLOW_MS)
