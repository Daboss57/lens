from __future__ import annotations

from typing import Any

from lens.config import LensConfig
from lens.transport import HTTPTraceTransport
from lens.types import TraceEvent


class LensClient:
    def __init__(
        self,
        config: LensConfig | None = None,
        *,
        transport: HTTPTraceTransport | None = None,
    ) -> None:
        self.config = config or LensConfig.from_env()
        self.transport = transport or HTTPTraceTransport(self.config)

    @classmethod
    def from_env(cls) -> "LensClient":
        return cls(config=LensConfig.from_env())

    def capture(self, event: TraceEvent) -> bool:
        try:
            return self.transport.send(event)
        except Exception:
            return False

    def record(self, **payload: Any) -> bool:
        try:
            return self.capture(TraceEvent(**payload))
        except Exception:
            return False

    def close(self) -> None:
        self.transport.close()


class AsyncLensClient:
    def __init__(
        self,
        config: LensConfig | None = None,
        *,
        transport: HTTPTraceTransport | None = None,
    ) -> None:
        self.config = config or LensConfig.from_env()
        self.transport = transport or HTTPTraceTransport(self.config)

    @classmethod
    def from_env(cls) -> "AsyncLensClient":
        return cls(config=LensConfig.from_env())

    async def capture(self, event: TraceEvent) -> bool:
        try:
            return await self.transport.send_async(event)
        except Exception:
            return False

    async def record(self, **payload: Any) -> bool:
        try:
            return await self.capture(TraceEvent(**payload))
        except Exception:
            return False

    async def aclose(self) -> None:
        await self.transport.aclose()
