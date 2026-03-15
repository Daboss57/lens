# LENS Python SDK

Python tracing SDK for LENS local LLM observability.

## Install

Core client only:

```bash
pip install lens-python
```

With provider SDKs:

```bash
pip install "lens-python[providers]"
```

Or install one provider extra at a time:

```bash
pip install "lens-python[openai]"
pip install "lens-python[anthropic]"
pip install "lens-python[gemini]"
```

## Quick Start

```python
from lens import LensClient

client = LensClient.from_env()

client.record(
    provider="openai",
    model="gpt-5.4",
    request={"messages": [{"role": "user", "content": "hello"}]},
    response={"content": "hi"},
    prompt_tokens=42,
    completion_tokens=8,
    latency_ms=512,
    status="success",
)
```

## Environment

- `LENS_ENABLED`
- `LENS_API_URL`
- `LENS_INGEST_PATH`
- `LENS_TIMEOUT_SECONDS`

## Provider Wrappers

- `lens.openai`
- `lens.anthropic`
- `lens.gemini`

Importing those modules patches the provider clients so model calls can be captured and forwarded to the LENS API.

## Behavior

- sync + async client support
- silent-fail trace delivery when LENS is unavailable
- compatible with OpenAI, Anthropic, and Gemini wrappers
