from __future__ import annotations

import os
from dataclasses import dataclass, field


def _parse_bool(value: str | None, *, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() not in {"0", "false", "no", "off", ""}


@dataclass(frozen=True)
class LensConfig:
    enabled: bool = True
    base_url: str = "http://localhost:8100"
    ingest_path: str = "/api/v1/traces"
    timeout_seconds: float = 1.5
    headers: dict[str, str] = field(default_factory=dict)

    @property
    def ingest_url(self) -> str:
        return f"{self.base_url.rstrip('/')}{self.ingest_path}"

    @classmethod
    def from_env(cls) -> "LensConfig":
        return cls(
            enabled=_parse_bool(os.getenv("LENS_ENABLED"), default=True),
            base_url=os.getenv("LENS_API_URL", "http://localhost:8100"),
            ingest_path=os.getenv("LENS_INGEST_PATH", "/api/v1/traces"),
            timeout_seconds=float(os.getenv("LENS_TIMEOUT_SECONDS", "1.5")),
        )
