from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any

import pytest

from lens._gemini import patch_gemini


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@dataclass
class FakeUsageMetadata:
    prompt_token_count: int
    candidates_token_count: int
    total_token_count: int


class FakeGeminiResponse:
    def __init__(self, model: str, text: str = "ok") -> None:
        self.model = model
        self.text = text
        self.usage_metadata = FakeUsageMetadata(
            prompt_token_count=30,
            candidates_token_count=9,
            total_token_count=39,
        )

    def model_dump(self) -> dict[str, Any]:
        return {
            "model": self.model,
            "text": self.text,
            "usage_metadata": {
                "prompt_token_count": self.usage_metadata.prompt_token_count,
                "candidates_token_count": self.usage_metadata.candidates_token_count,
                "total_token_count": self.usage_metadata.total_token_count,
            },
        }


class FakeModels:
    def generate_content(
        self, *, model: str, contents: Any, config: dict[str, Any] | None = None
    ) -> Any:
        if contents == "explode":
            raise RuntimeError("rate limit")
        return FakeGeminiResponse(model)


class FakeAsyncModels:
    async def generate_content(
        self, *, model: str, contents: Any, config: dict[str, Any] | None = None
    ) -> Any:
        if contents == "explode":
            raise TimeoutError("request timeout")
        return FakeGeminiResponse(model)


class FakeGoogleGenAIClient:
    def __init__(self) -> None:
        self.models = FakeModels()
        self.aio = SimpleNamespace(models=FakeAsyncModels())


class FakeGenerativeModel:
    def __init__(self, model_name: str) -> None:
        self.model_name = model_name

    def generate_content(
        self, contents: Any, generation_config: dict[str, Any] | None = None
    ) -> Any:
        if contents == "explode":
            raise RuntimeError("rate limit")
        return FakeGeminiResponse(self.model_name)

    async def generate_content_async(
        self, contents: Any, generation_config: dict[str, Any] | None = None
    ) -> Any:
        if contents == "explode":
            raise TimeoutError("request timeout")
        return FakeGeminiResponse(self.model_name)


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


def test_google_genai_client_wrapper_captures_success() -> None:
    sync_recorder = SyncRecorder()
    async_recorder = AsyncRecorder()
    module = SimpleNamespace(Client=FakeGoogleGenAIClient)
    patch_gemini(module, lens_client=sync_recorder, async_lens_client=async_recorder)

    client = module.Client()
    response = client.models.generate_content(
        model="gemini-2.5-pro",
        contents="hello",
        config={"metadata": {"session_id": "gemini-session", "user_id": "user-3"}},
    )

    assert response.model == "gemini-2.5-pro"
    assert len(sync_recorder.events) == 1
    event = sync_recorder.events[0]
    assert event.provider == "gemini"
    assert event.prompt_tokens == 30
    assert event.completion_tokens == 9
    assert event.session_id == "gemini-session"


def test_google_genai_client_wrapper_accepts_lens_specific_kwargs() -> None:
    sync_recorder = SyncRecorder()
    async_recorder = AsyncRecorder()
    module = SimpleNamespace(Client=FakeGoogleGenAIClient)
    patch_gemini(module, lens_client=sync_recorder, async_lens_client=async_recorder)

    client = module.Client()
    response = client.models.generate_content(
        model="gemini-2.5-pro",
        contents="hello",
        lens_session_id="gemini-lens-session",
        lens_user_id="gemini-user",
        lens_metadata={"source": "test"},
    )

    assert response.model == "gemini-2.5-pro"
    event = sync_recorder.events[0]
    assert event.session_id == "gemini-lens-session"
    assert event.user_id == "gemini-user"
    assert event.metadata["source"] == "test"


@pytest.mark.anyio
async def test_google_genai_async_wrapper_captures_success() -> None:
    sync_recorder = SyncRecorder()
    async_recorder = AsyncRecorder()
    module = SimpleNamespace(Client=FakeGoogleGenAIClient)
    patch_gemini(module, lens_client=sync_recorder, async_lens_client=async_recorder)

    client = module.Client()
    response = await client.aio.models.generate_content(
        model="gemini-3.1-pro-preview",
        contents="hello",
        config={"metadata": {"session_id": "gemini-async"}},
    )

    assert response.model == "gemini-3.1-pro-preview"
    assert len(async_recorder.events) == 1
    assert async_recorder.events[0].status == "success"


def test_deprecated_generative_model_wrapper_captures_failure() -> None:
    sync_recorder = SyncRecorder()
    async_recorder = AsyncRecorder()
    module = SimpleNamespace(GenerativeModel=FakeGenerativeModel)
    patch_gemini(module, lens_client=sync_recorder, async_lens_client=async_recorder)

    model = module.GenerativeModel("gemini-2.5-flash")
    with pytest.raises(RuntimeError):
        model.generate_content("explode")

    assert len(sync_recorder.events) == 1
    assert sync_recorder.events[0].status == "rate_limit"
    assert sync_recorder.events[0].model == "gemini-2.5-flash"


@pytest.mark.anyio
async def test_deprecated_generative_model_async_wrapper_captures_failure() -> None:
    sync_recorder = SyncRecorder()
    async_recorder = AsyncRecorder()
    module = SimpleNamespace(GenerativeModel=FakeGenerativeModel)
    patch_gemini(module, lens_client=sync_recorder, async_lens_client=async_recorder)

    model = module.GenerativeModel("gemini-2.5-flash")
    with pytest.raises(TimeoutError):
        await model.generate_content_async("explode")

    assert len(async_recorder.events) == 1
    assert async_recorder.events[0].status == "timeout"
