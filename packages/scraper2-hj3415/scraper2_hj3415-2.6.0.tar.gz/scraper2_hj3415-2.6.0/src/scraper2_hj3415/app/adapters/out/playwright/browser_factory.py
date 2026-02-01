# scraper2_hj3415/app/adapters/out/playwright/browser_factory.py
from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import AsyncIterator

from scraper2_hj3415.app.ports.browser.browser_factory_port import BrowserFactoryPort
from scraper2_hj3415.app.ports.browser.browser_port import BrowserPort
from scraper2_hj3415.app.adapters.out.playwright.session import PlaywrightPageSession
from scraper2_hj3415.app.adapters.out.playwright.browser import PlaywrightBrowser


@dataclass
class _LeaseItem:
    session: PlaywrightPageSession
    browser: BrowserPort


class PlaywrightBrowserFactory(BrowserFactoryPort):
    """
    풀링 방식:
    - astart()에서 max_concurrency 만큼 세션/페이지/브라우저를 미리 생성
    - lease()는 큐에서 하나 빌려주고 반납받음
    - aclose()에서 모두 종료
    """

    def __init__(self, *, headless: bool, timeout_ms: int, max_concurrency: int = 2):
        self.headless = headless
        self.timeout_ms = timeout_ms
        self.max_concurrency = max_concurrency

        self._pool: asyncio.Queue[_LeaseItem] = asyncio.Queue(maxsize=max_concurrency)
        self._items: list[_LeaseItem] = []  # 종료용 레퍼런스
        self._started = False
        self._start_lock = asyncio.Lock()
        self._closed = False

    async def astart(self) -> None:
        """
        풀을 미리 채움.
        여러 번 호출돼도 1회만 초기화되도록 방어.
        """
        if self._started:
            return

        async with self._start_lock:
            if self._started:
                return
            if self._closed:
                raise RuntimeError("Factory is closed; cannot start again.")

            for _ in range(self.max_concurrency):
                session = PlaywrightPageSession(headless=self.headless, timeout_ms=self.timeout_ms)
                page = await session.start()
                browser = PlaywrightBrowser(page)

                item = _LeaseItem(session=session, browser=browser)
                self._items.append(item)
                await self._pool.put(item)

            self._started = True

    @asynccontextmanager
    async def lease(self) -> AsyncIterator[BrowserPort]:
        """
        브라우저 하나를 풀에서 빌려줌.
        사용 후 반드시 풀에 반납.
        """
        if self._closed:
            raise RuntimeError("Factory is closed; cannot lease.")
        if not self._started:
            await self.astart()

        item = await self._pool.get()
        try:
            yield item.browser
        finally:
            # close 중이면 반납하지 말고 그냥 종료 플로우에 맡김
            if not self._closed:
                await self._pool.put(item)

    async def aclose(self) -> None:
        """
        풀에 있는 모든 세션 종료.
        - 실행 중인 lease가 끝나기 전에 닫으면: 남아있는 세션만 닫히고,
          나중에 lease가 반납하려 할 때 _closed=True라 put이 안 되도록 처리.
        """
        if self._closed:
            return
        self._closed = True

        # 전체 세션 종료
        # (이미 대여 중인 애도 결국 같은 session 객체이므로 close 시도됨)
        for item in self._items:
            try:
                await item.session.close()
            except Exception:
                # 종료 단계에서는 예외 삼키는 게 보통 안전
                pass

        self._items.clear()

        # 큐 비우기 (참조 제거)
        try:
            while True:
                self._pool.get_nowait()
        except asyncio.QueueEmpty:
            pass


