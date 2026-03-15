from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any

import pytest

from lens._openai import patch_openai


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@dataclass
class FakeUsage:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class FakeResponse:
    def __init__(self, model: str, content: str = "hi") -> None:
        self.model = model
        self.content = content
        self.usage = FakeUsage(prompt_tokens=12, completion_tokens=4, total_tokens=16)

    def model_dump(self) -> dict[str, Any]:
        return {
            "model": self.model,
            "choices": [{"message": {"content": self.content}}],
            "usage": {
                "prompt_tokens": self.usage.prompt_tokens,
                "completion_tokens": self.usage.completion_tokens,
                "total_tokens": self.usage.total_tokens,
            },
        }


class FakeSyncCompletions:
    def create(self, **kwargs: Any) -> FakeResponse:
        if kwargs.get("messages", [{}])[0].get("content") == "explode":
            raise RuntimeError("rate limit exceeded")
        return FakeResponse(kwargs["model"])


class FakeAsyncCompletions:
    async def create(self, **kwargs: Any) -> FakeResponse:
        if kwargs.get("messages", [{}])[0].get("content") == "explode":
            raise TimeoutError("request timeout")
        return FakeResponse(kwargs["model"])


class FakeOpenAI:
    def __init__(self) -> None:
        self.chat = SimpleNamespace(completions=FakeSyncCompletions())


class FakeAsyncOpenAI:
    def __init__(self) -> None:
        self.chat = SimpleNamespace(completions=FakeAsyncCompletions())


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


def make_fake_openai_module() -> Any:
    return SimpleNamespace(OpenAI=FakeOpenAI, AsyncOpenAI=FakeAsyncOpenAI)


def test_sync_openai_wrapper_captures_successful_chat_completion() -> None:
    sync_recorder = SyncRecorder()
    async_recorder = AsyncRecorder()
    patch_openai(
        make_fake_openai_module(),
        lens_client=sync_recorder,
        async_lens_client=async_recorder,
    )

    client = FakeOpenAI()
    response = client.chat.completions.create(
        model="gpt-5.4",
        messages=[{"role": "user", "content": "hello"}],
        metadata={"session_id": "session-1", "feature": "chat"},
        user="user-1",
    )

    assert response.model == "gpt-5.4"
    assert len(sync_recorder.events) == 1
    event = sync_recorder.events[0]
    assert event.provider == "openai"
    assert event.model == "gpt-5.4"
    assert event.session_id == "session-1"
    assert event.user_id == "user-1"
    assert event.endpoint == "chat.completions.create"
    assert event.prompt_tokens == 12
    assert event.completion_tokens == 4


def test_sync_openai_wrapper_accepts_lens_specific_kwargs() -> None:
    sync_recorder = SyncRecorder()
    async_recorder = AsyncRecorder()
    patch_openai(
        make_fake_openai_module(),
        lens_client=sync_recorder,
        async_lens_client=async_recorder,
    )

    client = FakeOpenAI()
    response = client.chat.completions.create(
        model="gpt-5.4",
        messages=[{"role": "user", "content": "hello"}],
        lens_session_id="lens-session-1",
        lens_user_id="lens-user-1",
        lens_metadata={"source": "test"},
    )

    assert response.model == "gpt-5.4"
    event = sync_recorder.events[0]
    assert event.session_id == "lens-session-1"
    assert event.user_id == "lens-user-1"
    assert event.metadata["source"] == "test"


def test_sync_openai_wrapper_re_raises_and_captures_failure() -> None:
    sync_recorder = SyncRecorder()
    async_recorder = AsyncRecorder()
    patch_openai(
        make_fake_openai_module(),
        lens_client=sync_recorder,
        async_lens_client=async_recorder,
    )

    client = FakeOpenAI()
    with pytest.raises(RuntimeError):
        client.chat.completions.create(
            model="gpt-5.4",
            messages=[{"role": "user", "content": "explode"}],
        )

    assert len(sync_recorder.events) == 1
    event = sync_recorder.events[0]
    assert event.status == "rate_limit"
    assert event.error_msg == "rate limit exceeded"


@pytest.mark.anyio
async def test_async_openai_wrapper_captures_successful_chat_completion() -> None:
    sync_recorder = SyncRecorder()
    async_recorder = AsyncRecorder()
    module = make_fake_openai_module()
    patch_openai(module, lens_client=sync_recorder, async_lens_client=async_recorder)

    client = module.AsyncOpenAI()
    response = await client.chat.completions.create(
        model="gpt-5.4",
        messages=[{"role": "user", "content": "hello"}],
        metadata={"session_id": "async-session"},
    )

    assert response.model == "gpt-5.4"
    assert len(async_recorder.events) == 1
    event = async_recorder.events[0]
    assert event.status == "success"
    assert event.session_id == "async-session"


@pytest.mark.anyio
async def test_async_openai_wrapper_re_raises_and_captures_failure() -> None:
    sync_recorder = SyncRecorder()
    async_recorder = AsyncRecorder()
    module = make_fake_openai_module()
    patch_openai(module, lens_client=sync_recorder, async_lens_client=async_recorder)

    client = module.AsyncOpenAI()
    with pytest.raises(TimeoutError):
        await client.chat.completions.create(
            model="gpt-5.4",
            messages=[{"role": "user", "content": "explode"}],
        )

    assert len(async_recorder.events) == 1
    event = async_recorder.events[0]
    assert event.status == "timeout"
    assert event.error_msg == "request timeout"
