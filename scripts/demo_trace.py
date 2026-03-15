from __future__ import annotations

from datetime import datetime, timezone
from random import choice, randint, random

from lens import LensClient

PROVIDERS = [
    ("openai", "gpt-5.4"),
    ("anthropic", "claude-sonnet-4-6"),
    ("gemini", "gemini-2.5-pro"),
]

STATUSES = ["success", "success", "success", "timeout", "rate_limit"]


def main() -> None:
    client = LensClient.from_env()
    provider, model = choice(PROVIDERS)
    status = choice(STATUSES)
    prompt_tokens = randint(120, 1400)
    completion_tokens = randint(40, 320) if status == "success" else 0
    session_id = f"demo-session-{randint(1, 4)}"

    response = (
        {"content": "Synthetic response from the local LENS demo flow."}
        if status == "success"
        else None
    )
    error_msg = None
    if status == "timeout":
        error_msg = "request timeout"
    elif status == "rate_limit":
        error_msg = "rate limit exceeded"

    client.record(
        trace_id=f"demo-{provider}-{datetime.now(timezone.utc).timestamp()}",
        session_id=session_id,
        user_id="demo-user",
        provider=provider,
        model=model,
        endpoint="demo.synthetic.generate",
        request={
            "messages": [{"role": "user", "content": "Show me a demo trace"}],
            "temperature": round(0.2 + random() * 0.8, 2),
        },
        response=response,
        metadata={"session_id": session_id, "source": "demo-script"},
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        latency_ms=randint(180, 3200),
        status=status,
        error_msg=error_msg,
    )
    client.close()


if __name__ == "__main__":
    main()
