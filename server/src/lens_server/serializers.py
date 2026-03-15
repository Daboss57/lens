from __future__ import annotations

from lens_server.models import Trace


def trace_to_dict(trace: Trace) -> dict[str, object]:
    return {
        "trace_id": trace.trace_id,
        "session_id": trace.session_id,
        "user_id": trace.user_id,
        "provider": trace.provider,
        "model": trace.model,
        "endpoint": trace.endpoint,
        "request": trace.request,
        "response": trace.response,
        "metadata": trace.metadata_json,
        "prompt_tokens": trace.prompt_tokens,
        "completion_tokens": trace.completion_tokens,
        "total_tokens": trace.total_tokens,
        "cost_usd": trace.cost_usd,
        "latency_ms": trace.latency_ms,
        "status": trace.status,
        "error_type": trace.error_type,
        "error_msg": trace.error_msg,
        "timestamp": trace.timestamp,
    }
