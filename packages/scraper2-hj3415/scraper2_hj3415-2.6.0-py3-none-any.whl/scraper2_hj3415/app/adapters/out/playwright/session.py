# scraper2_hj3415/app/adapters/out/playwright/session.py
from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from typing import Optional

from playwright.async_api import (
    async_playwright,
    Browser,
    BrowserContext,
    Page,
    Error as PWError,
)


def _install_playwright_browsers(*names: str) -> None:
    """python -m playwright install [names...] 를 코드에서 실행"""
    subprocess.run([sys.executable, "-m", "playwright", "install", *names], check=True)

    if sys.platform.startswith("linux"):
        # deps는 실패해도 그냥 진행 (환경에 따라 불필요/권한 문제)
        try:
            subprocess.run(
                [sys.executable, "-m", "playwright", "install-deps"], check=True
            )
        except Exception:
            pass


def _need_install(e: Exception) -> bool:
    msg = str(e)
    return (
        "Executable doesn't exist" in msg
        or "download new browsers" in msg
        or "playwright install" in msg
        or "Please run the following command" in msg
    )


@dataclass
class PlaywrightPageSession:
    """
    main에서 쓰기 쉬운 세션:
        s = PlaywrightPageSession(headless=True)
        page = await s.start()
        ...
        await s.close()
    """

    headless: bool = True
    browser_name: str = "chromium"
    timeout_ms: int = 10_000
    auto_install: bool = True  # env PW_SKIP_AUTO_INSTALL=1이면 자동으로 꺼짐

    # runtime resources
    pw: Optional[object] = None
    browser: Optional[Browser] = None
    context: Optional[BrowserContext] = None
    page: Optional[Page] = None

    async def start(self) -> Page:
        if self.page is not None:
            return self.page  # 이미 시작된 경우 재사용(원치 않으면 제거)

        self.pw = await async_playwright().start()
        try:
            browser_type = getattr(self.pw, self.browser_name)

            try:
                self.browser = await browser_type.launch(headless=self.headless)
            except PWError as e:
                should_auto = self.auto_install and os.getenv("PW_SKIP_AUTO_INSTALL") != "1"
                if should_auto and _need_install(e):
                    # pw 종료 -> 설치 -> pw 재시작
                    await self.pw.stop()
                    _install_playwright_browsers(self.browser_name)
                    self.pw = await async_playwright().start()
                    browser_type = getattr(self.pw, self.browser_name)
                    self.browser = await browser_type.launch(headless=self.headless)
                else:
                    raise

            self.context = await self.browser.new_context()
            self.page = await self.context.new_page()
            self.page.set_default_timeout(self.timeout_ms)
            return self.page

        except Exception:
            # start 중간에 터지면 자원 정리
            await self.close()
            raise

    async def close(self) -> None:
        # 역순 정리 (page는 context close 시 같이 정리됨)
        if self.context is not None:
            try:
                await self.context.close()
            except Exception:
                pass
            finally:
                self.context = None
                self.page = None

        if self.browser is not None:
            try:
                await self.browser.close()
            except Exception:
                pass
            finally:
                self.browser = None

        if self.pw is not None:
            try:
                await self.pw.stop()
            except Exception:
                pass
            finally:
                self.pw = None