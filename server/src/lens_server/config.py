from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[3]


def _default_database_path() -> Path:
    return BASE_DIR / "data" / "lens.db"


def _parse_origins(raw_value: str | None) -> tuple[str, ...]:
    if not raw_value:
        return (
            "http://localhost:4200",
            "http://127.0.0.1:4200",
        )
    return tuple(origin.strip() for origin in raw_value.split(",") if origin.strip())


@dataclass(frozen=True)
class Settings:
    app_name: str
    api_v1_prefix: str
    host: str
    port: int
    database_path: Path
    cors_origins: tuple[str, ...]

    @property
    def database_url(self) -> str:
        db_path = self.database_path
        if not db_path.is_absolute():
            db_path = BASE_DIR / db_path
        return f"sqlite:///{db_path.as_posix()}"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    db_path = Path(os.getenv("LENS_DB_PATH", str(_default_database_path())))
    return Settings(
        app_name="LENS API",
        api_v1_prefix="/api/v1",
        host=os.getenv("LENS_API_HOST", "0.0.0.0"),
        port=int(os.getenv("LENS_API_PORT", "8100")),
        database_path=db_path,
        cors_origins=_parse_origins(os.getenv("LENS_CORS_ORIGINS")),
    )
