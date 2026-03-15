from __future__ import annotations

from typing import Any

from lens._gemini import patch_gemini

patch_gemini()


def __getattr__(name: str) -> Any:
    if name == "patch_gemini":
        return patch_gemini
    raise AttributeError(name)


def __dir__() -> list[str]:
    return ["patch_gemini"]
