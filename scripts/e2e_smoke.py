from __future__ import annotations

import time

import httpx

from lens import LensClient


def wait_for_api(base_url: str, timeout_seconds: float = 20.0) -> None:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            response = httpx.get(f"{base_url}/api/v1/health", timeout=2.0)
            if response.status_code == 200:
                return
        except Exception:
            pass
        time.sleep(0.5)
    raise RuntimeError("API did not become healthy in time")


def main() -> None:
    base_url = "http://localhost:8100"
    wait_for_api(base_url)

    client = LensClient.from_env()
    trace_id = f"e2e-smoke-{int(time.time())}"
    client.record(
        trace_id=trace_id,
        session_id="e2e-session",
        user_id="e2e-user",
        provider="openai",
        model="gpt-5.4",
        endpoint="e2e.smoke",
        request={"messages": [{"role": "user", "content": "Run smoke test"}]},
        response={"content": "Smoke test ok"},
        metadata={"session_id": "e2e-session", "source": "e2e-smoke"},
        prompt_tokens=120,
        completion_tokens=25,
        latency_ms=420,
        status="success",
    )
    client.close()

    with httpx.Client(timeout=5.0) as http_client:
        traces_response = http_client.get(
            f"{base_url}/api/v1/traces", params={"session_id": "e2e-session"}
        )
        traces_response.raise_for_status()
        traces = traces_response.json()
        assert any(trace["trace_id"] == trace_id for trace in traces), (
            "Trace not found in traces endpoint"
        )

        session_response = http_client.get(f"{base_url}/api/v1/sessions/e2e-session")
        session_response.raise_for_status()
        session_detail = session_response.json()
        assert session_detail["session"]["trace_count"] >= 1, "Session count did not update"

    print(f"E2E smoke passed for {trace_id}")


if __name__ == "__main__":
    main()
