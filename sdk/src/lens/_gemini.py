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

PATCHED_FLAG = "__lens_gemini_patched__"
ORIGINAL_METHOD_ATTR = "__lens_gemini_original_method__"
ORIGINAL_INIT_ATTR = "__lens_gemini_original_init__"


def _extract_model_name(
    request_kwargs: dict[str, Any],
    response_payload: dict[str, Any] | None,
    *,
    fallback_model: Any = None,
) -> str:
    response_model = None if response_payload is None else response_payload.get("model")
    return str(response_model or request_kwargs.get("model") or fallback_model or "unknown")


def _extract_metadata(request_kwargs: dict[str, Any]) -> dict[str, Any] | None:
    config = request_kwargs.get("config")
    if isinstance(config, dict) and isinstance(config.get("metadata"), dict):
        return config["metadata"]

    generation_config = request_kwargs.get("generation_config")
    if isinstance(generation_config, dict) and isinstance(generation_config.get("metadata"), dict):
        return generation_config["metadata"]

    metadata = request_kwargs.get("metadata")
    return metadata if isinstance(metadata, dict) else None


def _build_success_event(
    *,
    provider_model: Any,
    request_kwargs: dict[str, Any],
    request_payload: dict[str, Any],
    response: Any,
    latency_ms: int,
    endpoint: str,
) -> TraceEvent:
    response_payload = response_to_dict(response)
    prompt_tokens, completion_tokens, total_tokens = extract_usage(response)
    metadata = _extract_metadata(request_kwargs)
    return TraceEvent(
        provider="gemini",
        model=_extract_model_name(request_kwargs, response_payload, fallback_model=provider_model),
        request=request_payload,
        response=response_payload,
        session_id=extract_session_id(metadata),
        user_id=extract_user_id(metadata),
        endpoint=endpoint,
        metadata=metadata,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        latency_ms=latency_ms,
        status="success",
    )


def _build_error_event(
    *,
    provider_model: Any,
    request_kwargs: dict[str, Any],
    request_payload: dict[str, Any],
    latency_ms: int,
    exc: Exception,
    endpoint: str,
) -> TraceEvent:
    metadata = _extract_metadata(request_kwargs)
    return TraceEvent(
        provider="gemini",
        model=_extract_model_name(request_kwargs, None, fallback_model=provider_model),
        request=request_payload,
        response=None,
        session_id=extract_session_id(metadata),
        user_id=extract_user_id(metadata),
        endpoint=endpoint,
        metadata=metadata,
        latency_ms=latency_ms,
        status=error_status(exc),
        error_msg=str(exc),
    )


def _patch_bound_method(
    owner: Any,
    method_name: str,
    recorder: Any,
    *,
    asynchronous: bool,
    endpoint: str,
    provider_model: Any = None,
) -> None:
    original_name = f"{ORIGINAL_METHOD_ATTR}_{method_name}"
    method = getattr(owner, original_name, None)
    if method is None:
        method = getattr(owner, method_name, None)
        if not callable(method):
            return
        setattr(owner, original_name, method)

    if asynchronous:

        @wraps(method)
        async def wrapped(*args: Any, **kwargs: Any) -> Any:
            started_at = perf_counter()
            request_kwargs = dict(kwargs)
            request_payload = build_request_payload(args, request_kwargs)
            try:
                response = await method(*args, **kwargs)
            except Exception as exc:
                latency_ms = int((perf_counter() - started_at) * 1000)
                await recorder.capture(
                    _build_error_event(
                        provider_model=provider_model,
                        request_kwargs=request_kwargs,
                        request_payload=request_payload,
                        latency_ms=latency_ms,
                        exc=exc,
                        endpoint=endpoint,
                    )
                )
                raise

            latency_ms = int((perf_counter() - started_at) * 1000)
            await recorder.capture(
                _build_success_event(
                    provider_model=provider_model,
                    request_kwargs=request_kwargs,
                    request_payload=request_payload,
                    response=response,
                    latency_ms=latency_ms,
                    endpoint=endpoint,
                )
            )
            return response

    else:

        @wraps(method)
        def wrapped(*args: Any, **kwargs: Any) -> Any:
            started_at = perf_counter()
            request_kwargs = dict(kwargs)
            request_payload = build_request_payload(args, request_kwargs)
            try:
                response = method(*args, **kwargs)
            except Exception as exc:
                latency_ms = int((perf_counter() - started_at) * 1000)
                recorder.capture(
                    _build_error_event(
                        provider_model=provider_model,
                        request_kwargs=request_kwargs,
                        request_payload=request_payload,
                        latency_ms=latency_ms,
                        exc=exc,
                        endpoint=endpoint,
                    )
                )
                raise

            latency_ms = int((perf_counter() - started_at) * 1000)
            recorder.capture(
                _build_success_event(
                    provider_model=provider_model,
                    request_kwargs=request_kwargs,
                    request_payload=request_payload,
                    response=response,
                    latency_ms=latency_ms,
                    endpoint=endpoint,
                )
            )
            return response

    setattr(wrapped, PATCHED_FLAG, True)
    setattr(owner, method_name, wrapped)


def _patch_google_genai_client(client: Any, recorder: Any) -> None:
    models = getattr(client, "models", None)
    if models is not None:
        _patch_bound_method(
            models,
            "generate_content",
            recorder,
            asynchronous=False,
            endpoint="models.generate_content",
        )


def _patch_google_genai_async_client(client: Any, recorder: Any) -> None:
    aio = getattr(client, "aio", None)
    models = getattr(aio, "models", None) if aio is not None else None
    if models is not None:
        _patch_bound_method(
            models,
            "generate_content",
            recorder,
            asynchronous=True,
            endpoint="models.generate_content",
        )


def _patch_google_genai_client_class(
    client_class: type[Any], recorder: Any, async_recorder: Any
) -> None:
    original_init = getattr(client_class, ORIGINAL_INIT_ATTR, None)
    if original_init is None:
        original_init = client_class.__init__
        setattr(client_class, ORIGINAL_INIT_ATTR, original_init)

    @wraps(original_init)
    def wrapped_init(self: Any, *args: Any, **kwargs: Any) -> None:
        original_init(self, *args, **kwargs)
        _patch_google_genai_client(self, recorder)
        _patch_google_genai_async_client(self, async_recorder)

    setattr(client_class, "__init__", wrapped_init)


def _patch_deprecated_generative_model(
    model_class: type[Any], recorder: Any, async_recorder: Any
) -> None:
    original_init = getattr(model_class, ORIGINAL_INIT_ATTR, None)
    if original_init is None:
        original_init = model_class.__init__
        setattr(model_class, ORIGINAL_INIT_ATTR, original_init)

    @wraps(original_init)
    def wrapped_init(self: Any, *args: Any, **kwargs: Any) -> None:
        original_init(self, *args, **kwargs)
        provider_model = getattr(self, "model_name", None)
        _patch_bound_method(
            self,
            "generate_content",
            recorder,
            asynchronous=False,
            endpoint="generate_content",
            provider_model=provider_model,
        )
        _patch_bound_method(
            self,
            "generate_content_async",
            async_recorder,
            asynchronous=True,
            endpoint="generate_content_async",
            provider_model=provider_model,
        )

    setattr(model_class, "__init__", wrapped_init)


def patch_gemini(
    target: Any | None = None,
    *,
    lens_client: LensClient | Any | None = None,
    async_lens_client: AsyncLensClient | Any | None = None,
) -> Any:
    lens_client = lens_client or LensClient.from_env()
    async_lens_client = async_lens_client or AsyncLensClient.from_env()

    targets = [target] if target is not None else []
    if not targets:
        for module_name in ("google.genai", "google.generativeai"):
            try:
                targets.append(import_module(module_name))
            except Exception:
                continue

    for current_target in targets:
        if current_target is None:
            continue

        client_class = getattr(current_target, "Client", None)
        if isinstance(client_class, type):
            _patch_google_genai_client_class(client_class, lens_client, async_lens_client)

        generative_model = getattr(current_target, "GenerativeModel", None)
        if isinstance(generative_model, type):
            _patch_deprecated_generative_model(generative_model, lens_client, async_lens_client)

    return target
