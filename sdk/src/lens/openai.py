from __future__ import annotations

from importlib import import_module
from typing import Any

from lens._openai import patch_openai

_openai = patch_openai(import_module("openai"))


def __getattr__(name: str) -> Any:
    return getattr(_openai, name)


def __dir__() -> list[str]:
    return sorted(set(dir(_openai)) | {"patch_openai"})
