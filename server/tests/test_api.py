from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient


def make_trace_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "trace_id": "trace-openai-1",
        "session_id": "session-a",
        "provider": "openai",
        "model": "gpt-4o-mini",
        "request": {"messages": [{"role": "user", "content": "hello"}]},
        "response": {"content": "hi there"},
        "prompt_tokens": 100,
        "completion_tokens": 50,
        "latency_ms": 321,
        "status": "success",
    }
    payload.update(overrides)
    return payload


def test_ingest_trace_and_read_it_back(client: TestClient) -> None:
    payload = make_trace_payload()

    response = client.post("/api/v1/traces", json=payload)

    assert response.status_code == 201
    body = response.json()
    assert body["trace_id"] == payload["trace_id"]
    assert body["total_tokens"] == 150
    assert body["cost_usd"] > 0
    assert body["status"] == "success"

    trace_response = client.get(f"/api/v1/traces/{payload['trace_id']}")
    assert trace_response.status_code == 200
    assert trace_response.json()["provider"] == "openai"


def test_duplicate_trace_id_returns_conflict(client: TestClient) -> None:
    payload = make_trace_payload(
        trace_id="duplicate-trace",
        provider="anthropic",
        model="claude-3-5-sonnet",
        response={"content": "hi"},
        prompt_tokens=10,
        completion_tokens=5,
        latency_ms=90,
    )

    assert client.post("/api/v1/traces", json=payload).status_code == 201
    duplicate = client.post("/api/v1/traces", json=payload)

    assert duplicate.status_code == 409


def test_stats_sessions_and_failures_endpoints(client: TestClient) -> None:
    client.post(
        "/api/v1/traces",
        json=make_trace_payload(
            trace_id="trace-success-1",
            response={"content": "hello"},
            prompt_tokens=80,
            completion_tokens=20,
            latency_ms=200,
        ),
    )
    client.post(
        "/api/v1/traces",
        json=make_trace_payload(
            trace_id="trace-failure-1",
            provider="gemini",
            model="gemini-1.5-flash",
            request={"contents": ["hi"]},
            response={},
            prompt_tokens=70,
            completion_tokens=0,
            latency_ms=440,
            status="timeout",
            error_msg="request timeout",
        ),
    )

    overview = client.get("/api/v1/stats/overview")
    sessions = client.get("/api/v1/sessions")
    session_detail = client.get("/api/v1/sessions/session-a")
    failures = client.get("/api/v1/stats/failures")
    costs = client.get("/api/v1/stats/costs", params={"group_by": "provider"})

    assert overview.status_code == 200
    assert overview.json()["total_traces"] == 2
    assert overview.json()["failed_traces"] == 1

    assert sessions.status_code == 200
    assert sessions.json()[0]["trace_count"] == 2

    assert session_detail.status_code == 200
    assert len(session_detail.json()["traces"]) == 2

    assert failures.status_code == 200
    assert failures.json()["total_failures"] == 1
    assert failures.json()["by_error_type"][0]["key"] == "timeout"

    assert costs.status_code == 200
    assert {bucket["key"] for bucket in costs.json()["buckets"]} == {"openai", "gemini"}


def test_websocket_broadcasts_new_trace(client: TestClient) -> None:
    with client.websocket_connect("/ws/traces") as websocket:
        connected = websocket.receive_json()
        assert connected["event"] == "connected"

        response = client.post(
            "/api/v1/traces",
            json=make_trace_payload(
                trace_id="trace-stream-1",
                session_id="session-stream",
                request={"messages": [{"role": "user", "content": "stream"}]},
                response={"content": "ok"},
                prompt_tokens=20,
                completion_tokens=10,
                latency_ms=111,
            ),
        )

        assert response.status_code == 201

        event = websocket.receive_json()
        assert event["event"] == "trace.created"
        assert event["data"]["trace_id"] == "trace-stream-1"


def test_demo_trace_endpoint_creates_and_broadcasts_trace(client: TestClient) -> None:
    with client.websocket_connect("/ws/traces") as websocket:
        connected = websocket.receive_json()
        assert connected["event"] == "connected"

        response = client.post("/api/v1/demo/trace")
        assert response.status_code == 201

        body = response.json()
        assert body["trace_id"].startswith("demo-")
        assert body["provider"] in {"openai", "anthropic", "gemini"}

        event = websocket.receive_json()
        assert event["event"] == "trace.created"
        assert event["data"]["trace_id"] == body["trace_id"]


def test_traces_endpoint_applies_query_filters_and_pagination(client: TestClient) -> None:
    now = datetime.now(timezone.utc)
    payloads = [
        make_trace_payload(
            trace_id="trace-filter-newest",
            session_id="session-filter",
            timestamp=now.isoformat(),
        ),
        make_trace_payload(
            trace_id="trace-filter-second",
            session_id="session-filter",
            timestamp=(now - timedelta(hours=1)).isoformat(),
        ),
        make_trace_payload(
            trace_id="trace-filter-old",
            session_id="session-filter",
            timestamp=(now - timedelta(days=10)).isoformat(),
        ),
        make_trace_payload(
            trace_id="trace-filter-provider-miss",
            session_id="session-filter",
            provider="anthropic",
            model="claude-3-5-sonnet",
            timestamp=(now - timedelta(minutes=30)).isoformat(),
        ),
        make_trace_payload(
            trace_id="trace-filter-status-miss",
            session_id="session-filter",
            status="timeout",
            error_msg="request timeout",
            timestamp=(now - timedelta(minutes=15)).isoformat(),
        ),
    ]

    for payload in payloads:
        response = client.post("/api/v1/traces", json=payload)
        assert response.status_code == 201

    filtered = client.get(
        "/api/v1/traces",
        params={
            "provider": "openai",
            "model": "gpt-4o-mini",
            "status": "success",
            "session_id": "session-filter",
            "days": 2,
            "limit": 1,
            "offset": 1,
        },
    )

    assert filtered.status_code == 200
    assert [trace["trace_id"] for trace in filtered.json()] == ["trace-filter-second"]


@pytest.mark.parametrize(
    ("path", "params"),
    [
        ("/api/v1/traces", {"days": 0}),
        ("/api/v1/traces", {"limit": 0}),
        ("/api/v1/traces", {"offset": -1}),
        ("/api/v1/stats/costs", {"group_by": "region"}),
        ("/api/v1/stats/costs", {"days": 0}),
        ("/api/v1/stats/failures", {"limit": 0}),
    ],
)
def test_invalid_query_params_return_422(
    client: TestClient, path: str, params: dict[str, int | str]
) -> None:
    response = client.get(path, params=params)

    assert response.status_code == 422


@pytest.mark.parametrize(
    "payload",
    [
        make_trace_payload(provider="invalid-provider"),
        make_trace_payload(model=""),
        make_trace_payload(prompt_tokens=-1),
        make_trace_payload(request="not-an-object"),
        make_trace_payload(response="not-an-object"),
        make_trace_payload(metadata="not-an-object"),
    ],
)
def test_ingest_trace_rejects_invalid_payloads(
    client: TestClient, payload: dict[str, object]
) -> None:
    response = client.post("/api/v1/traces", json=payload)

    assert response.status_code == 422


def test_ingest_trace_rejects_malformed_json(client: TestClient) -> None:
    response = client.post(
        "/api/v1/traces",
        content='{"trace_id": "broken",',
        headers={"content-type": "application/json"},
    )

    assert response.status_code == 422
