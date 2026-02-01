# scraper2_hj3415/app/adapters/out/playwright/browser.py
from __future__ import annotations

from typing import Any
from io import StringIO
import pandas as pd
from playwright.async_api import Page, TimeoutError as PwTimeoutError
import asyncio
import time
from logging_hj3415 import logger


class PlaywrightBrowser:
    def __init__(self, page: Page):
        self._page = page

    async def _wait_for_network_quiet(self, *, timeout_ms: int = 10_000) -> None:
        # networkidle은 사이트에 따라 영원히 안 올 수도 있어서 try로 감싸는 게 안전
        logger.debug("wait for network quiet")
        try:
            await self._page.wait_for_load_state("networkidle", timeout=timeout_ms)
        except Exception:
            # networkidle이 안 와도 다음 단계(앵커 wait)가 더 중요함
            return

    async def wait_table_nth_ready(
        self,
        table_selector: str,
        *,
        index: int,
        min_rows: int = 1,
        timeout_ms: int = 20_000,
        poll_ms: int = 200,
    ) -> None:
        logger.debug("wait for table nth_ready")
        table = self._page.locator(table_selector).nth(index)
        await table.wait_for(state="attached", timeout=timeout_ms)

        # html = await table.evaluate("el => el.outerHTML")
        # logger.debug(f"TABLE HTML:\n{html}")

        rows = table.locator("tbody tr")
        deadline = time.monotonic() + timeout_ms / 1000

        cnt = 0
        while time.monotonic() < deadline:
            try:
                cnt = await rows.count()
            except Exception:
                cnt = 0

            if cnt >= min_rows:
                return

            await asyncio.sleep(poll_ms / 1000)

        logger.warning(f"table rows timeout: last_cnt={cnt}, need>={min_rows}")
        raise TimeoutError(f"nth table not ready: index={index}, rows<{min_rows}")

    async def title(self) -> str:
        return await self._page.title()

    async def current_url(self) -> str:
        return self._page.url

    async def goto_and_wait_for_stable(
        self, url: str, timeout_ms: int = 10_000
    ) -> None:
        logger.info(f"goto: {url}")
        await self._page.goto(url, timeout=timeout_ms, wait_until="domcontentloaded")
        await self._wait_for_network_quiet(timeout_ms=timeout_ms // 2)

    async def reload(self, *, timeout_ms: int = 10_000) -> None:
        logger.info("reload")
        await self._page.reload(timeout=timeout_ms, wait_until="domcontentloaded")

    async def sleep_ms(self, ms: int) -> None:
        await asyncio.sleep(ms / 1000)

    async def wait_attached(self, selector: str, *, timeout_ms: int = 10_000) -> None:
        await self._page.locator(selector).first.wait_for(
            state="attached", timeout=timeout_ms
        )

    async def wait_visible(self, selector: str, *, timeout_ms: int = 10_000) -> None:
        await self._page.locator(selector).first.wait_for(
            state="visible", timeout=timeout_ms
        )

    async def click(
        self,
        selector: str,
        *,
        index: int = 0,
        timeout_ms: int = 4_000,
        force: bool = False,
    ) -> None:
        loc = self._page.locator(selector).nth(index)
        await loc.click(timeout=timeout_ms, force=force)

    async def try_click(
        self,
        selector: str,
        *,
        index: int = 0,
        timeout_ms: int = 1_500,
        force: bool = False,
    ) -> bool:
        loc = self._page.locator(selector).nth(index)
        try:
            await loc.click(timeout=timeout_ms, trial=True, force=force)
            return True
        except PwTimeoutError:
            return False

    async def count(self, selector: str) -> int:
        return await self._page.locator(selector).count()

    async def scroll_into_view(self, selector: str, *, index: int = 0) -> None:
        # 선택한 요소가 화면에 보이도록 스크롤을 자동으로 내려준다.
        await self._page.locator(selector).nth(index).scroll_into_view_if_needed()

    async def text_content_first(self, selector: str) -> str:
        # selector 첫 번째 요소의 text_content()를 반환
        return (await self._page.locator(selector).first.text_content()) or ""

    async def all_texts(self, selector: str) -> list[str]:
        # selector로 잡히는 모든 요소를 all_text_contents()로 가져옴
        loc = self._page.locator(selector)
        return await loc.all_text_contents()

    async def get_text_by_text(self, needle: str) -> str:
        """
        페이지에서 주어진 텍스트(needle)를 포함하는 요소 중
        첫 번째 요소의 text_content를 반환한다.

        - 요소가 없으면 빈 문자열 반환
        - 부분 일치 기준
        """
        return (await self._page.get_by_text(needle).first.text_content()) or ""

    async def inner_text(self, selector: str) -> str:
        """
        selector에 해당하는 첫 번째 요소의 innerText를 반환한다.

        - 요소가 DOM에 attach될 때까지 대기
        - 화면에 보이는 텍스트 기준(innerText)
        """
        return await self._page.locator(selector).first.inner_text()

    async def outer_html_nth(self, selector: str, index: int) -> str:
        """
        selector로 매칭되는 요소 중 index번째 요소의 outerHTML을 반환한다.

        - index는 0-based
        - 요소가 없으면 playwright 예외 발생
        """
        loc = self._page.locator(selector).nth(index)
        # index가 범위를 벗어나면 playwright가 에러를 내는데,
        # 필요하면 여기서 더 친절한 에러로 감싸도 됨.
        return await loc.evaluate("el => el.outerHTML")

    async def wait_table_text_changed(
        self,
        table_selector: str,
        *,
        index: int,
        prev_text: str | None,
        min_rows: int = 1,
        min_lines: int = 50,
        timeout_sec: float = 12.0,
        poll_sec: float = 0.2,
    ) -> str:
        """
        지정한 table(nth)의 innerText가 '유효한 상태'가 되고,
        이전 텍스트(prev_text)와 달라질 때까지 대기한 뒤 반환한다.

        동작 순서:
        1) tbody row 개수 기준으로 테이블이 최소한 로딩되었는지 보장
        2) innerText를 주기적으로 폴링하며
           - 최소 라인 수(min_lines)를 만족하고
           - prev_text가 None이거나, prev_text와 다른 경우 반환

        특징:
        - DOM이 붙었지만 데이터가 아직 비어 있는 상태를 배제
        - 클릭/토글 이후 실제 데이터 변경을 안정적으로 감지
        - 타임아웃 시 마지막으로 관측된 텍스트를 반환

        반환값:
        - 변경된(innerText) 문자열
        """

        # 0) 최초/혹은 불안정할 때는 row 기준으로 'ready'를 먼저 확보
        await self.wait_table_nth_ready(
            table_selector,
            index=index,
            min_rows=min_rows,
            timeout_ms=int(timeout_sec * 1000),
            poll_ms=int(poll_sec * 1000),
        )

        # 1) 그 다음 텍스트 기반으로 '유효 + 변경'을 기다림
        start = time.monotonic()
        last_text = ""

        while True:
            loc = self._page.locator(table_selector).nth(index)
            try:
                text = await loc.inner_text()
            except Exception:
                text = ""

            lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
            is_valid = len(lines) >= min_lines

            if is_valid:
                last_text = text
                if prev_text is None or text != prev_text:
                    return text

            if time.monotonic() - start >= timeout_sec:
                return last_text

            await asyncio.sleep(poll_sec)

    async def is_attached(self, selector: str, *, index: int = 0) -> bool:
        """
        selector의 nth(index) 요소가 DOM에 존재하는지(attached) 여부를 반환한다.
        요소가 없거나 접근 중 예외가 발생하면 False를 반환한다.
        """
        try:
            loc = self._page.locator(selector).nth(index)
            return await loc.count() > 0
        except Exception:
            return False

    async def computed_style(self, selector: str, *, index: int = 0, prop: str) -> str:
        """
        selector의 nth(index) 요소에 대해,
        CSS 계산값(getComputedStyle)의 특정 속성(prop)을 문자열로 반환한다.
        (예: display, visibility, opacity 등)
        """
        loc = self._page.locator(selector).nth(index)
        # attached 보장하고 싶으면 여기서 wait_for(state="attached") 추가 가능
        return await loc.evaluate(
            "(el, prop) => getComputedStyle(el)[prop] || ''", prop
        )

    async def count_in_nth(
        self,
        scope_selector: str,
        *,
        scope_index: int,
        inner_selector: str,
    ) -> int:
        """
        scope_selector의 nth(scope_index) 범위 안에서
        inner_selector에 매칭되는 요소 개수를 반환한다.
        """
        scope = self._page.locator(scope_selector).nth(scope_index)
        return await scope.locator(inner_selector).count()

    async def eval_in_nth_first(
        self,
        scope_selector: str,
        *,
        scope_index: int,
        inner_selector: str,
        expression: str,
    ) -> Any:
        """
        scope(nth) 내부의 inner_selector.first element를 잡고 JS expression을 실행한다.

        expression 예:
          - "el => window.getComputedStyle(el).display"
          - "el => el.getAttribute('data-content') || ''"
          - "el => el.innerText"
        """
        scope = self._page.locator(scope_selector).nth(scope_index)
        loc = scope.locator(inner_selector).first

        # 매칭되는 게 없으면 None
        if await loc.count() == 0:
            return None

        return await loc.evaluate(expression)

    async def inner_text_in_nth(
        self,
        scope_selector: str,
        *,
        scope_index: int,
        inner_selector: str,
        inner_index: int = 0,
        timeout_ms: int = 10_000,
    ) -> str:
        """
        scope(nth) 내부에서 inner_selector(nth)의 innerText를 반환.
        - innerText: 렌더링 기준(줄바꿈/숨김 반영)
        """
        scope = self._page.locator(scope_selector).nth(scope_index)
        inner = scope.locator(inner_selector).nth(inner_index)

        # 요소가 늦게 뜨는 케이스 대응
        await inner.wait_for(state="attached", timeout=timeout_ms)

        try:
            return (await inner.inner_text()) or ""
        except Exception:
            # inner_text 자체가 실패하는 순간(사라짐/리렌더)도 있어서 안전하게
            return ""

    async def text_content_in_nth(
        self,
        scope_selector: str,
        *,
        scope_index: int,
        inner_selector: str,
        inner_index: int = 0,
        timeout_ms: int = 10_000,
    ) -> str:
        """
        scope(nth) 내부에서 inner_selector(nth)의 textContent를 반환.
        - textContent: DOM 기준(숨김 텍스트 포함 가능)
        """
        scope = self._page.locator(scope_selector).nth(scope_index)
        inner = scope.locator(inner_selector).nth(inner_index)

        await inner.wait_for(state="attached", timeout=timeout_ms)

        try:
            return (await inner.text_content()) or ""
        except Exception:
            return ""

    async def table_records(
        self,
        table_selector: str,
        *,
        header: int | list[int] | None = 0,
    ) -> list[dict[str, Any]]:
        await self.wait_attached(table_selector)

        table = self._page.locator(table_selector).first
        html = await table.evaluate("el => el.outerHTML")

        try:
            df = pd.read_html(StringIO(html), header=header)[0]
        except Exception as e:
            raise RuntimeError(f"pd.read_html failed: {type(e).__name__}: {e}") from e

        # 문자열 컬럼일 때만 정규화
        if all(isinstance(c, str) for c in df.columns):
            if "항목" in df.columns:
                df["항목"] = (
                    df["항목"].astype(str).str.replace("펼치기", "").str.strip()
                )

            df.columns = (
                df.columns.astype(str)
                .str.replace("연간컨센서스보기", "", regex=False)
                .str.replace("연간컨센서스닫기", "", regex=False)
                .str.replace("(IFRS연결)", "", regex=False)
                .str.replace("(IFRS별도)", "", regex=False)
                .str.replace("(GAAP개별)", "", regex=False)
                .str.replace("(YoY)", "", regex=False)
                .str.replace("(QoQ)", "", regex=False)
                .str.replace("(E)", "", regex=False)
                .str.replace(".", "", regex=False)
                .str.strip()
            )

        return df.where(pd.notnull(df), None).to_dict(orient="records")
