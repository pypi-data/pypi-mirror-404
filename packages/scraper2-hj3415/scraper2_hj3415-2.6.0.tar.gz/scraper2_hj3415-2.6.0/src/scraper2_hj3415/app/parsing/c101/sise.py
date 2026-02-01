# scraper2_hj3415/app/parsing/c101/sise.py
from __future__ import annotations

from scraper2_hj3415.app.ports.browser.browser_port import BrowserPort
from common_hj3415.utils import clean_text
from ._sise_normalizer import normalize_sise_kv_map

_SISE_TABLE = "#cTB11"

async def parse_c101_sise_table(browser: BrowserPort) -> dict[str, str]:
    """
    #cTB11 시세정보 테이블을 th(항목명) -> td(값) dict로 추출한다.
    - 화면에 보이는 텍스트 기준(innerText)
    """
    await browser.wait_attached(_SISE_TABLE)

    row_cnt = await browser.count_in_nth(
        _SISE_TABLE,
        scope_index=0,
        inner_selector="tbody tr",
    )

    out: dict[str, str] = {}

    for i in range(1, row_cnt + 1):  # nth-child는 1-based
        row_sel = f"tbody tr:nth-child({i})"

        key = await browser.inner_text_in_nth(
            _SISE_TABLE,
            scope_index=0,
            inner_selector=f"{row_sel} th",
            inner_index=0,
        )
        val = await browser.inner_text_in_nth(
            _SISE_TABLE,
            scope_index=0,
            inner_selector=f"{row_sel} td",
            inner_index=0,
        )

        k = clean_text(key)
        v = clean_text(val)
        if k:
            out[k] = v
    raw = out
    return normalize_sise_kv_map(raw)

