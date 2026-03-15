from __future__ import annotations

import httpx

from lens.config import LensConfig
from lens.types import TraceEvent


class HTTPTraceTransport:
    def __init__(
        self,
        config: LensConfig,
        *,
        client: httpx.Client | None = None,
        async_client: httpx.AsyncClient | None = None,
    ) -> None:
        self.config = config
        self._client = client or httpx.Client(timeout=config.timeout_seconds)
        self._async_client = async_client or httpx.AsyncClient(timeout=config.timeout_seconds)
        self._owns_client = client is None
        self._owns_async_client = async_client is None

    def send(self, event: TraceEvent) -> bool:
        if not self.config.enabled:
            return False

        try:
            response = self._client.post(
                self.config.ingest_url,
                json=event.to_payload(),
                headers=self.config.headers,
            )
            response.raise_for_status()
            return True
        except Exception:
            return False

    async def send_async(self, event: TraceEvent) -> bool:
        if not self.config.enabled:
            return False

        try:
            response = await self._async_client.post(
                self.config.ingest_url,
                json=event.to_payload(),
                headers=self.config.headers,
            )
            response.raise_for_status()
            return True
        except Exception:
            return False

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    async def aclose(self) -> None:
        if self._owns_async_client:
            await self._async_client.aclose()
