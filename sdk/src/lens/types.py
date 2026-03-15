from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

TraceStatus = Literal["success", "error", "timeout", "rate_limit", "empty_response"]
TraceProvider = Literal["openai", "anthropic", "gemini"]


def _normalize_timestamp(timestamp: datetime) -> datetime:
    if timestamp.tzinfo is None:
        return timestamp.replace(tzinfo=timezone.utc)
    return timestamp.astimezone(timezone.utc)


def make_json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, datetime):
        return _normalize_timestamp(value).isoformat().replace("+00:00", "Z")
    if isinstance(value, dict):
        return {str(key): make_json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [make_json_safe(item) for item in value]
    return str(value)


@dataclass(slots=True)
class TraceEvent:
    provider: TraceProvider
    model: str
    request: dict[str, Any] = field(default_factory=dict)
    response: dict[str, Any] | None = None
    trace_id: str = field(default_factory=lambda: str(uuid4()))
    session_id: str | None = None
    user_id: str | None = None
    endpoint: str | None = None
    metadata: dict[str, Any] | None = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int | None = None
    latency_ms: int = 0
    status: TraceStatus = "success"
    error_msg: str | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if self.total_tokens is None:
            self.total_tokens = self.prompt_tokens + self.completion_tokens
        self.timestamp = _normalize_timestamp(self.timestamp)

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "trace_id": self.trace_id,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "provider": self.provider,
            "model": self.model,
            "endpoint": self.endpoint,
            "request": make_json_safe(self.request),
            "response": make_json_safe(self.response),
            "metadata": make_json_safe(self.metadata),
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "latency_ms": self.latency_ms,
            "status": self.status,
            "error_msg": self.error_msg,
            "timestamp": self.timestamp.isoformat().replace("+00:00", "Z"),
        }
        return {key: value for key, value in payload.items() if value is not None}
