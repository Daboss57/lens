from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any

import pytest

from lens._anthropic import patch_anthropic


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@dataclass
class FakeAnthropicUsage:
    input_tokens: int
    output_tokens: int


class FakeAnthropicResponse:
    def __init__(self, model: str, text: str = "done") -> None:
        self.model = model
        self.content = [{"type": "text", "text": text}]
        self.usage = FakeAnthropicUsage(input_tokens=20, output_tokens=6)

    def model_dump(self) -> dict[str, Any]:
        return {
            "model": self.model,
            "content": self.content,
            "usage": {
                "input_tokens": self.usage.input_tokens,
                "output_tokens": self.usage.output_tokens,
            },
        }


class FakeSyncMessages:
    def create(self, **kwargs: Any) -> FakeAnthropicResponse:
        if kwargs.get("messages", [{}])[0].get("content") == "boom":
            raise RuntimeError("rate limit")
        return FakeAnthropicResponse(kwargs["model"])


class FakeAsyncMessages:
    async def create(self, **kwargs: Any) -> FakeAnthropicResponse:
        if kwargs.get("messages", [{}])[0].get("content") == "boom":
            raise TimeoutError("request timeout")
        return FakeAnthropicResponse(kwargs["model"])


class FakeAnthropic:
    def __init__(self) -> None:
        self.messages = SimpleNamespace(create=FakeSyncMessages().create)


class FakeAsyncAnthropic:
    def __init__(self) -> None:
        self.messages = SimpleNamespace(create=FakeAsyncMessages().create)


class SyncRecorder:
    def __init__(self) -> None:
        self.events: list[Any] = []

    def capture(self, event: Any) -> bool:
        self.events.append(event)
        return True


class AsyncRecorder:
    def __init__(self) -> None:
        self.events: list[Any] = []

    async def capture(self, event: Any) -> bool:
        self.events.append(event)
        return True


def make_fake_module() -> Any:
    return SimpleNamespace(Anthropic=FakeAnthropic, AsyncAnthropic=FakeAsyncAnthropic)


def test_sync_anthropic_wrapper_captures_success() -> None:
    sync_recorder = SyncRecorder()
    async_recorder = AsyncRecorder()
    module = make_fake_module()
    patch_anthropic(module, lens_client=sync_recorder, async_lens_client=async_recorder)

    client = module.Anthropic()
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=100,
        messages=[{"role": "user", "content": "hello"}],
        metadata={"session_id": "anthropic-session", "user_id": "user-2"},
    )

    assert response.model == "claude-sonnet-4-6"
    assert len(sync_recorder.events) == 1
    event = sync_recorder.events[0]
    assert event.provider == "anthropic"
    assert event.prompt_tokens == 20
    assert event.completion_tokens == 6
    assert event.session_id == "anthropic-session"
    assert event.user_id == "user-2"


def test_sync_anthropic_wrapper_captures_failure_and_reraises() -> None:
    sync_recorder = SyncRecorder()
    async_recorder = AsyncRecorder()
    module = make_fake_module()
    patch_anthropic(module, lens_client=sync_recorder, async_lens_client=async_recorder)

    client = module.Anthropic()
    with pytest.raises(RuntimeError):
        client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=100,
            messages=[{"role": "user", "content": "boom"}],
        )

    assert len(sync_recorder.events) == 1
    assert sync_recorder.events[0].status == "rate_limit"


@pytest.mark.anyio
async def test_async_anthropic_wrapper_captures_success() -> None:
    sync_recorder = SyncRecorder()
    async_recorder = AsyncRecorder()
    module = make_fake_module()
    patch_anthropic(module, lens_client=sync_recorder, async_lens_client=async_recorder)

    client = module.AsyncAnthropic()
    response = await client.messages.create(
        model="claude-opus-4-6",
        max_tokens=100,
        messages=[{"role": "user", "content": "hello"}],
        metadata={"session_id": "async-anthropic"},
    )

    assert response.model == "claude-opus-4-6"
    assert len(async_recorder.events) == 1
    assert async_recorder.events[0].status == "success"


@pytest.mark.anyio
async def test_async_anthropic_wrapper_captures_failure_and_reraises() -> None:
    sync_recorder = SyncRecorder()
    async_recorder = AsyncRecorder()
    module = make_fake_module()
    patch_anthropic(module, lens_client=sync_recorder, async_lens_client=async_recorder)

    client = module.AsyncAnthropic()
    with pytest.raises(TimeoutError):
        await client.messages.create(
            model="claude-opus-4-6",
            max_tokens=100,
            messages=[{"role": "user", "content": "boom"}],
        )

    assert len(async_recorder.events) == 1
    assert async_recorder.events[0].status == "timeout"
