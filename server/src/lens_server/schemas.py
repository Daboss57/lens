from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, NonNegativeInt, model_validator


class TraceCreate(BaseModel):
    trace_id: str | None = Field(default=None, max_length=64)
    session_id: str | None = Field(default=None, max_length=255)
    user_id: str | None = Field(default=None, max_length=255)
    provider: Literal["openai", "anthropic", "gemini"]
    model: str = Field(min_length=1, max_length=255)
    endpoint: str | None = Field(default=None, max_length=255)
    request: dict[str, Any] = Field(default_factory=dict)
    response: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None
    prompt_tokens: NonNegativeInt = 0
    completion_tokens: NonNegativeInt = 0
    total_tokens: NonNegativeInt | None = None
    latency_ms: NonNegativeInt = 0
    status: Literal["success", "error", "timeout", "rate_limit", "empty_response"] = "success"
    error_msg: str | None = None
    timestamp: datetime | None = None

    @model_validator(mode="after")
    def populate_total_tokens(self) -> "TraceCreate":
        if self.total_tokens is None:
            self.total_tokens = self.prompt_tokens + self.completion_tokens
        return self


class TraceRead(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    trace_id: str
    session_id: str | None = None
    user_id: str | None = None
    provider: str
    model: str
    endpoint: str | None = None
    request: dict[str, Any]
    response: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float
    latency_ms: int
    status: str
    error_type: str | None = None
    error_msg: str | None = None
    timestamp: datetime


class SessionSummary(BaseModel):
    session_id: str
    trace_count: int
    success_count: int
    failure_count: int
    total_cost_usd: float
    started_at: datetime
    last_seen_at: datetime


class SessionDetail(BaseModel):
    session: SessionSummary
    traces: list[TraceRead]


class ProviderOverview(BaseModel):
    provider: str
    trace_count: int
    total_cost_usd: float


class OverviewStats(BaseModel):
    total_traces: int
    successful_traces: int
    failed_traces: int
    total_cost_usd: float
    average_latency_ms: float
    providers: list[ProviderOverview]


class CostBucket(BaseModel):
    key: str
    trace_count: int
    cost_usd: float
    prompt_tokens: int
    completion_tokens: int


class CostsResponse(BaseModel):
    group_by: Literal["day", "provider", "model"]
    buckets: list[CostBucket]


class CountBreakdown(BaseModel):
    key: str
    count: int


class FailureStats(BaseModel):
    total_failures: int
    by_error_type: list[CountBreakdown]
    by_provider: list[CountBreakdown]
    recent_failures: list[TraceRead]


class HealthResponse(BaseModel):
    status: str
    database_path: str
