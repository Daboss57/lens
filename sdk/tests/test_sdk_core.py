from __future__ import annotations

from datetime import datetime

import httpx
import pytest

from lens import AsyncLensClient, LensClient, LensConfig, TraceEvent
from lens.transport import HTTPTraceTransport


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


def test_config_reads_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LENS_ENABLED", "false")
    monkeypatch.setenv("LENS_API_URL", "http://example.test:9999")
    monkeypatch.setenv("LENS_INGEST_PATH", "/custom/traces")
    monkeypatch.setenv("LENS_TIMEOUT_SECONDS", "0.75")

    config = LensConfig.from_env()

    assert config.enabled is False
    assert config.ingest_url == "http://example.test:9999/custom/traces"
    assert config.timeout_seconds == 0.75


def test_trace_event_serializes_to_server_shape() -> None:
    event = TraceEvent(
        provider="openai",
        model="gpt-5.4",
        request={"messages": [{"role": "user", "content": "hello"}]},
        response={"content": "hi", "generated_at": datetime(2026, 3, 14, 1, 2, 3)},
        metadata={"tags": {"demo", "test"}},
        prompt_tokens=10,
        completion_tokens=5,
        latency_ms=123,
    )

    payload = event.to_payload()

    assert payload["provider"] == "openai"
    assert payload["total_tokens"] == 15
    assert payload["response"]["generated_at"].endswith("Z")
    assert sorted(payload["metadata"]["tags"]) == ["demo", "test"]


def test_sync_client_posts_trace_payload() -> None:
    seen: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["body"] = request.read().decode("utf-8")
        return httpx.Response(201, json={"ok": True})

    transport = HTTPTraceTransport(
        LensConfig(),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
        async_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )
    client = LensClient(transport=transport)

    result = client.capture(
        TraceEvent(provider="openai", model="gpt-5.4", request={"messages": []})
    )

    assert result is True
    assert seen["url"] == "http://localhost:8100/api/v1/traces"
    assert "gpt-5.4" in str(seen["body"])

    client.close()


def test_sync_client_swallows_transport_failures() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("boom")

    transport = HTTPTraceTransport(
        LensConfig(),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
        async_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )
    client = LensClient(transport=transport)

    assert client.record(provider="openai", model="gpt-5.4", request={"messages": []}) is False

    client.close()


@pytest.mark.anyio
async def test_async_client_posts_trace_payload() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(201, json={"received": request.url.path})

    transport = HTTPTraceTransport(
        LensConfig(),
        client=httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(201))),
        async_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )
    client = AsyncLensClient(transport=transport)

    result = await client.record(
        provider="gemini", model="gemini-2.5-pro", request={"contents": []}
    )

    assert result is True

    await client.aclose()
