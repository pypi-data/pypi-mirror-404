# scraper2_hj3415/app/ports/browser/browser_factory_port.py
from __future__ import annotations
from typing import Protocol, AsyncContextManager

from scraper2_hj3415.app.ports.browser.browser_port import BrowserPort

class BrowserFactoryPort(Protocol):
    def lease(self) -> AsyncContextManager[BrowserPort]: ...
    async def aclose(self) -> None: ...