from __future__ import annotations

from importlib import import_module
from typing import Any

from lens._anthropic import patch_anthropic

_anthropic = patch_anthropic(import_module("anthropic"))


def __getattr__(name: str) -> Any:
    return getattr(_anthropic, name)


def __dir__() -> list[str]:
    return sorted(set(dir(_anthropic)) | {"patch_anthropic"})
