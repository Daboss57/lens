from __future__ import annotations

import uvicorn

from lens_server.config import get_settings


def main() -> None:
    settings = get_settings()
    uvicorn.run(
        "lens_server.main:app",
        host=settings.host,
        port=settings.port,
        reload=False,
    )


if __name__ == "__main__":
    main()
