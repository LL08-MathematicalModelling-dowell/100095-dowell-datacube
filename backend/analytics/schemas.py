from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field, field_validator


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class HttpRequestSchema(BaseModel):
    user_id: str
    method: str
    path: str
    status_code: int
    duration_ms: float
    timestamp: datetime = Field(default_factory=utc_now)
    success: bool

    @field_validator("method")
    @classmethod
    def valid_method(cls, v: str) -> str:
        allowed = ("GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS")
        if v not in allowed:
            raise ValueError("Invalid HTTP method")
        return v


class DatabaseContextSchema(BaseModel):
    user_id: str
    db_id: Optional[str] = None
    collection: str = "system"
    operation_type: str
    document_count: int = 0
    query_complexity: str = "simple"
    timestamp: datetime = Field(default_factory=utc_now)


class PerformanceMetricsSchema(BaseModel):
    user_id: str
    request_size_bytes: int = 0
    response_size_bytes: int = 0
    throughput_bytes_per_sec: float = 0.0
    warning: Optional[str] = None
    timestamp: datetime = Field(default_factory=utc_now)


class ClientInfoSchema(BaseModel):
    user_id: str
    client_ip: str = ""
    user_agent: str = ""
    content_type: Optional[str] = None
    timestamp: datetime = Field(default_factory=utc_now)


class ErrorSchema(BaseModel):
    user_id: str
    status_code: int
    error_type: str
    error_message: Optional[str] = None
    timestamp: datetime = Field(default_factory=utc_now)


class MongoDetailSchema(BaseModel):
    user_id: str
    inserted_count: Optional[int] = None
    modified_count: Optional[int] = None
    deleted_count: Optional[int] = None
    returned_documents: Optional[int] = None
    timestamp: datetime = Field(default_factory=utc_now)


class SlowQuerySchema(BaseModel):
    user_id: str
    query_details: dict
    duration_ms: float
    threshold_ms: int
    collection: str
    db_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=utc_now)


class DailyAggregateSchema(BaseModel):
    user_id: str
    date: str
    total_requests: int = 0
    avg_duration_ms: float = 0.0
    error_rate: float = 0.0
    top_collections: list = Field(default_factory=list)
    top_endpoints: list = Field(default_factory=list)
