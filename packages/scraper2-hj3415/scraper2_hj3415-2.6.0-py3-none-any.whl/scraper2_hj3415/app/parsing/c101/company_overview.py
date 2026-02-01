# scraper2_hj3415/app/parsing/c101/company_overview.py
from __future__ import annotations

import re
from typing import Any
from scraper2_hj3415.app.ports.browser.browser_port import BrowserPort
from common_hj3415.utils import clean_text

# 정규표현식
_DATE_RE = re.compile(r"(\d{4}\.\d{2}\.\d{2})")  # YYYY.MM.DD

async def parse_c101_company_overview(browser: BrowserPort) -> dict[str, Any]:
    """
    '기업개요' 섹션에서
    - 기준일자([기준:YYYY.MM.DD])
    - 개요 문장들(li.dot_cmp)
    을 추출한다.
    """
    out: dict[str, Any] = {}

    기준_sel = "div.header-table p"
    개요_ul_sel = "div.cmp_comment ul.dot_cmp"
    개요_li_sel = "div.cmp_comment ul.dot_cmp > li.dot_cmp"

    # 1) 기준일자
    await browser.wait_attached(기준_sel)
    raw = clean_text(await browser.text_content_first(기준_sel))

    m = _DATE_RE.search(raw)
    out["기준일자"] = m.group(1) if m else raw

    # 2) 개요 문장들
    await browser.wait_attached(개요_ul_sel)
    li_texts = await browser.all_texts(개요_li_sel)

    lines: list[str] = []
    for t in li_texts:
        ct = clean_text(t)
        if ct:
            lines.append(ct)

    # out["개요_리스트"] = lines # 일단 필요 없음
    out["개요"] = "".join(
        lines
    )  # 정책: 저장용이면 join("") 유지, 표시용이면 "\n".join 고려

    return out
