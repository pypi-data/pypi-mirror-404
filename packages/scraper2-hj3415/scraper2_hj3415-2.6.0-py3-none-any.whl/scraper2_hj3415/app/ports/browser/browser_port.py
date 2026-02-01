# scraper2_hj3415/app/ports/browser/browser_port.py
from __future__ import annotations

from typing import Protocol, Any


class BrowserPort(Protocol):
    async def wait_table_nth_ready(
            self,
            table_selector: str,
            *,
            index: int,
            min_rows: int = 1,
            timeout_ms: int = 20_000,
            poll_ms: int = 200,
    ) -> None: ...
    async def title(self) -> str: ...
    async def current_url(self) -> str: ...
    async def goto_and_wait_for_stable(self, url: str, timeout_ms: int = 10_000) -> None: ...
    async def reload(self, *, timeout_ms: int = 10_000) -> None: ...
    async def sleep_ms(self, ms: int) -> None: ...
    async def wait_attached(
        self, selector: str, *, timeout_ms: int = 10_000
    ) -> None: ...
    async def wait_visible(
        self, selector: str, *, timeout_ms: int = 10_000
    ) -> None: ...
    async def click(
        self,
        selector: str,
        *,
        index: int = 0,
        timeout_ms: int = 4_000,
        force: bool = False,
    ) -> None: ...
    async def try_click(
        self,
        selector: str,
        *,
        index: int = 0,
        timeout_ms: int = 1_500,
        force: bool = False,
    ) -> bool: ...
    async def count(self, selector: str) -> int: ...
    async def scroll_into_view(self, selector: str, *, index: int = 0) -> None: ...
    async def text_content_first(self, selector: str) -> str: ...
    async def all_texts(self, selector: str) -> list[str]: ...
    async def get_text_by_text(self, needle: str) -> str: ...
    async def inner_text(self, selector: str) -> str: ...
    async def outer_html_nth(self, selector: str, index: int) -> str: ...
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
    ) -> str: ...
    async def is_attached(self, selector: str, *, index: int = 0) -> bool: ...
    async def computed_style(
        self, selector: str, *, index: int = 0, prop: str
    ) -> str: ...
    async def count_in_nth(
        self,
        scope_selector: str,
        *,
        scope_index: int,
        inner_selector: str,
    ) -> int: ...
    async def eval_in_nth_first(
        self,
        scope_selector: str,
        *,
        scope_index: int,
        inner_selector: str,
        expression: str,
    ) -> Any: ...
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
        scope_selector의 nth(scope_index) 요소 안에서
        inner_selector의 nth(inner_index) 요소의 innerText를 반환.
        (렌더링 기준 텍스트: 줄바꿈/스타일 영향 반영)
        """
        ...

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
        scope_selector의 nth(scope_index) 요소 안에서
        inner_selector의 nth(inner_index) 요소의 textContent를 반환.
        (DOM 기준 텍스트: 숨김 텍스트도 포함될 수 있음)
        """
        ...

    async def table_records(
        self, table_selector: str, *, header: int | list[int] | None = 0
    ) -> list[dict[str, Any]]: ...
