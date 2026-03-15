from __future__ import annotations

from functools import wraps
from importlib import import_module
from time import perf_counter
from typing import Any

from lens._wrapper_utils import (
    error_status,
    extract_session_id,
    extract_usage,
    extract_user_id,
    request_payload as build_request_payload,
    response_to_dict,
)
from lens.client import AsyncLensClient, LensClient
from lens.types import TraceEvent

PATCHED_FLAG = "__lens_openai_patched__"
ORIGINAL_CREATE_ATTR = "__lens_openai_original_create__"
ORIGINAL_INIT_ATTR = "__lens_openai_original_init__"


def _extract_model_name(
    request_kwargs: dict[str, Any], response_payload: dict[str, Any] | None
) -> str:
    response_model = None if response_payload is None else response_payload.get("model")
    return str(response_model or request_kwargs.get("model") or "unknown")


def _build_success_event(
    *,
    request_kwargs: dict[str, Any],
    request_payload: dict[str, Any],
    response: Any,
    latency_ms: int,
) -> TraceEvent:
    response_payload = response_to_dict(response)
    prompt_tokens, completion_tokens, total_tokens = extract_usage(response)
    metadata = (
        request_kwargs.get("metadata") if isinstance(request_kwargs.get("metadata"), dict) else None
    )
    return TraceEvent(
        provider="openai",
        model=_extract_model_name(request_kwargs, response_payload),
        request=request_payload,
        response=response_payload,
        session_id=extract_session_id(metadata),
        user_id=extract_user_id(metadata, request_kwargs.get("user")),
        endpoint="chat.completions.create",
        metadata=metadata,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        latency_ms=latency_ms,
        status="success",
    )


def _build_error_event(
    *,
    request_kwargs: dict[str, Any],
    request_payload: dict[str, Any],
    latency_ms: int,
    exc: Exception,
) -> TraceEvent:
    metadata = (
        request_kwargs.get("metadata") if isinstance(request_kwargs.get("metadata"), dict) else None
    )
    return TraceEvent(
        provider="openai",
        model=str(request_kwargs.get("model") or "unknown"),
        request=request_payload,
        response=None,
        session_id=extract_session_id(metadata),
        user_id=extract_user_id(metadata, request_kwargs.get("user")),
        endpoint="chat.completions.create",
        metadata=metadata,
        latency_ms=latency_ms,
        status=error_status(exc),
        error_msg=str(exc),
    )


def _patch_completions_resource(resource: Any, recorder: Any, *, asynchronous: bool) -> None:
    create = getattr(resource, ORIGINAL_CREATE_ATTR, None)
    if create is None:
        create = getattr(resource, "create", None)
        if not callable(create):
            return
        setattr(resource, ORIGINAL_CREATE_ATTR, create)

    if not callable(create):
        return

    if asynchronous:

        @wraps(create)
        async def wrapped_create(*args: Any, **kwargs: Any) -> Any:
            started_at = perf_counter()
            request_kwargs = dict(kwargs)
            request_payload = build_request_payload(args, request_kwargs)
            try:
                response = await create(*args, **kwargs)
            except Exception as exc:
                latency_ms = int((perf_counter() - started_at) * 1000)
                await recorder.capture(
                    _build_error_event(
                        request_kwargs=request_kwargs,
                        request_payload=request_payload,
                        latency_ms=latency_ms,
                        exc=exc,
                    )
                )
                raise

            latency_ms = int((perf_counter() - started_at) * 1000)
            await recorder.capture(
                _build_success_event(
                    request_kwargs=request_kwargs,
                    request_payload=request_payload,
                    response=response,
                    latency_ms=latency_ms,
                )
            )
            return response

    else:

        @wraps(create)
        def wrapped_create(*args: Any, **kwargs: Any) -> Any:
            started_at = perf_counter()
            request_kwargs = dict(kwargs)
            request_payload = build_request_payload(args, request_kwargs)
            try:
                response = create(*args, **kwargs)
            except Exception as exc:
                latency_ms = int((perf_counter() - started_at) * 1000)
                recorder.capture(
                    _build_error_event(
                        request_kwargs=request_kwargs,
                        request_payload=request_payload,
                        latency_ms=latency_ms,
                        exc=exc,
                    )
                )
                raise

            latency_ms = int((perf_counter() - started_at) * 1000)
            recorder.capture(
                _build_success_event(
                    request_kwargs=request_kwargs,
                    request_payload=request_payload,
                    response=response,
                    latency_ms=latency_ms,
                )
            )
            return response

    setattr(wrapped_create, PATCHED_FLAG, True)
    setattr(resource, "create", wrapped_create)


def _patch_client_instance(instance: Any, recorder: Any, *, asynchronous: bool) -> None:
    chat = getattr(instance, "chat", None)
    completions = getattr(chat, "completions", None) if chat is not None else None
    if completions is None:
        return
    _patch_completions_resource(completions, recorder, asynchronous=asynchronous)


def _patch_client_class(client_class: type[Any], recorder: Any, *, asynchronous: bool) -> None:
    original_init = getattr(client_class, ORIGINAL_INIT_ATTR, None)
    if original_init is None:
        original_init = client_class.__init__
        setattr(client_class, ORIGINAL_INIT_ATTR, original_init)

    @wraps(original_init)
    def wrapped_init(self: Any, *args: Any, **kwargs: Any) -> None:
        original_init(self, *args, **kwargs)
        _patch_client_instance(self, recorder, asynchronous=asynchronous)

    setattr(client_class, "__init__", wrapped_init)
    setattr(client_class, PATCHED_FLAG, True)


def patch_openai(
    target: Any | None = None,
    *,
    lens_client: LensClient | Any | None = None,
    async_lens_client: AsyncLensClient | Any | None = None,
) -> Any:
    target = target or import_module("openai")
    lens_client = lens_client or LensClient.from_env()
    async_lens_client = async_lens_client or AsyncLensClient.from_env()

    if hasattr(target, "chat"):
        _patch_client_instance(target, lens_client, asynchronous=False)

    for class_name, recorder, asynchronous in (
        ("OpenAI", lens_client, False),
        ("Client", lens_client, False),
        ("AsyncOpenAI", async_lens_client, True),
        ("AsyncClient", async_lens_client, True),
    ):
        client_class = getattr(target, class_name, None)
        if isinstance(client_class, type):
            _patch_client_class(client_class, recorder, asynchronous=asynchronous)

    return target
