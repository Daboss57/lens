from __future__ import annotations

from datetime import datetime
from typing import Any, Iterable

from lens.types import make_json_safe


def response_to_dict(response: Any) -> dict[str, Any] | None:
    if response is None:
        return None
    if isinstance(response, dict):
        return make_json_safe(response)

    for method_name in ("model_dump", "to_dict", "dict"):
        method = getattr(response, method_name, None)
        if callable(method):
            try:
                payload = method()
            except TypeError:
                continue
            if isinstance(payload, dict):
                return make_json_safe(payload)

    raw = getattr(response, "__dict__", None)
    if isinstance(raw, dict) and raw:
        return make_json_safe({key: value for key, value in raw.items() if not key.startswith("_")})

    return {"value": make_json_safe(response)}


def request_payload(args: tuple[Any, ...], kwargs: dict[str, Any]) -> dict[str, Any]:
    payload = make_json_safe(dict(kwargs))
    if args:
        payload["_args"] = make_json_safe(list(args))
    return payload


def error_status(exc: Exception) -> str:
    message = f"{exc.__class__.__name__} {exc}".lower()
    if "rate" in message or "429" in message:
        return "rate_limit"
    if "timeout" in message or "timed out" in message:
        return "timeout"
    return "error"


def extract_session_id(metadata: dict[str, Any] | None) -> str | None:
    if not isinstance(metadata, dict):
        return None
    value = metadata.get("session_id")
    return None if value is None else str(value)


def extract_user_id(metadata: dict[str, Any] | None, fallback: Any = None) -> str | None:
    if fallback is not None:
        return str(fallback)
    if not isinstance(metadata, dict):
        return None
    value = metadata.get("user_id")
    return None if value is None else str(value)


def extract_usage(
    response: Any,
    *,
    prompt_keys: Iterable[str] = ("prompt_tokens", "input_tokens", "prompt_token_count"),
    completion_keys: Iterable[str] = (
        "completion_tokens",
        "output_tokens",
        "candidates_token_count",
    ),
    total_keys: Iterable[str] = ("total_tokens", "total_token_count"),
) -> tuple[int, int, int | None]:
    if response is None:
        return 0, 0, None

    usage = None
    if isinstance(response, dict):
        usage = response.get("usage") or response.get("usage_metadata")
    else:
        usage = getattr(response, "usage", None) or getattr(response, "usage_metadata", None)

    if usage is None:
        return 0, 0, None

    if not isinstance(usage, dict):
        usage = response_to_dict(usage) or {}

    prompt_tokens = _first_int(usage, prompt_keys)
    completion_tokens = _first_int(usage, completion_keys)
    total_tokens = _first_optional_int(usage, total_keys)
    if total_tokens is None and (prompt_tokens or completion_tokens):
        total_tokens = prompt_tokens + completion_tokens
    return prompt_tokens, completion_tokens, total_tokens


def _first_int(payload: dict[str, Any], keys: Iterable[str]) -> int:
    value = _first_optional_int(payload, keys)
    return 0 if value is None else value


def _first_optional_int(payload: dict[str, Any], keys: Iterable[str]) -> int | None:
    for key in keys:
        value = payload.get(key)
        if value is None:
            continue
        try:
            return int(value)
        except (TypeError, ValueError):
            continue
    return None
