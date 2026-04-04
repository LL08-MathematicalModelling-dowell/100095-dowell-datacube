from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field, validator


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

    @validator('method')
    def valid_method(cls, v):
        if v not in ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS']:
            raise ValueError('Invalid HTTP method')
        return v

class DatabaseContextSchema(BaseModel):
    user_id: str
    db_id: Optional[str] = None
    collection: str = "system"
    operation_type: str  # insert, query, update, delete, bulk_insert, etc.
    document_count: int = 0
    query_complexity: str = "simple"  # simple / complex

class PerformanceMetricsSchema(BaseModel):
    user_id: str
    request_size_bytes: int = 0
    response_size_bytes: int = 0
    throughput_bytes_per_sec: float = 0.0
    warning: Optional[str] = None  # "slow_request", "large_request"

class ClientInfoSchema(BaseModel):
    user_id: str
    client_ip: str = ""
    user_agent: str = ""
    content_type: Optional[str] = None

class ErrorSchema(BaseModel):
    user_id: str
    status_code: int
    error_type: str  # "client_error" or "server_error"
    error_message: Optional[str] = None
    timestamp: datetime = Field(default_factory=utc_now)

class MongoDetailSchema(BaseModel):
    user_id: str
    inserted_count: Optional[int] = None
    modified_count: Optional[int] = None
    deleted_count: Optional[int] = None
    returned_documents: Optional[int] = None

class SlowQuerySchema(BaseModel):
    user_id: str
    query_details: dict  # method, path, params snippet
    duration_ms: float
    threshold_ms: int
    collection: str
    db_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=utc_now)

# For daily aggregates (populated by a scheduled task)
class DailyAggregateSchema(BaseModel):
    user_id: str
    date: str  # YYYY-MM-DD
    total_requests: int = 0
    avg_duration_ms: float = 0.0
    error_rate: float = 0.0  # 0-1
    top_collections: list = []
    top_endpoints: list = []



# import json
# from dataclasses import dataclass, asdict
# from typing import Optional, Any
# from datetime import datetime

# @dataclass
# class HttpRequestLog:
#     """Basic HTTP request/response info."""
#     user_id: str
#     method: str
#     path: str
#     status_code: int
#     duration_ms: float
#     timestamp: int  # milliseconds since epoch
#     success: bool

#     def to_json(self) -> str:
#         return json.dumps(asdict(self))

# @dataclass
# class DatabaseContextLog:
#     """MongoDB operation context."""
#     db_id: Optional[str]
#     collection: str
#     operation_type: str  # insert, query, update, delete, etc.
#     document_count: int
#     query_complexity: str  # simple / complex

#     def to_json(self) -> str:
#         return json.dumps(asdict(self))

# @dataclass
# class PerformanceMetricsLog:
#     """Performance‑related numbers."""
#     request_size_bytes: int
#     response_size_bytes: int
#     throughput_bytes_per_sec: float
#     warning: Optional[str] = None  # 'slow_request', 'large_request', etc.

#     def to_json(self) -> str:
#         return json.dumps(asdict(self))

# @dataclass
# class ClientInfoLog:
#     """Client & network details."""
#     client_ip: str
#     user_agent: str
#     content_type: Optional[str]

#     def to_json(self) -> str:
#         return json.dumps(asdict(self))

# @dataclass
# class ErrorLog:
#     """Only logged when request fails (4xx/5xx)."""
#     status_code: int
#     error_type: str  # 'client_error' or 'server_error'
#     error_message: Optional[str] = None

#     def to_json(self) -> str:
#         return json.dumps(asdict(self))

# @dataclass
# class MongoOperationDetailLog:
#     """Optional: detailed MongoDB counts (inserted, modified, deleted, returned)."""
#     inserted_count: Optional[int] = None
#     modified_count: Optional[int] = None
#     deleted_count: Optional[int] = None
#     returned_documents: Optional[int] = None

#     def to_json(self) -> str:
#         # omit None values
#         data = {k: v for k, v in asdict(self).items() if v is not None}
#         return json.dumps(data)