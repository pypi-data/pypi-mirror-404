# scraper2_hj3415/app/parsing/c101/summary_cmp.py
from __future__ import annotations

from typing import Any
from scraper2_hj3415.app.ports.browser.browser_port import BrowserPort
from common_hj3415.utils import clean_text
from scraper2_hj3415.app.parsing._normalize.values import to_number


async def parse_c101_summary_cmp_table(browser: BrowserPort) -> dict[str, Any]:
    """
    <table class="cmp-table"> (회사 요약 테이블)에서 종목 기본 + EPS/BPS/PER... 등을 추출한다.

    반환 예:
    {
      "종목명": "삼성전자",
      "코드": "005930",
      "영문명": "SamsungElec",
      "시장": "KOSPI : 코스피 전기·전자",
      "WICS": "WICS : 반도체와반도체장비",
      "EPS": 4816,
      "BPS": 60632,
      "PER": 31.58,
      "업종PER": 21.93,
      "PBR": 2.51,
      "현금배당수익률": 0.95,
      "결산": "12월 결산",
    }
    """
    out: dict[str, Any] = {}

    # 테이블 존재 확인
    await browser.wait_attached("table.cmp-table")

    # --- 1) td0101: 종목명/코드/영문/시장/WICS ---
    out["종목명"] = clean_text(
        await browser.text_content_first("table.cmp-table td.td0101 span.name")
    )
    out["코드"] = clean_text(
        await browser.text_content_first("table.cmp-table td.td0101 b.num")
    )

    # td0101의 dt 텍스트들을 읽어 분류
    dt0101 = await browser.all_texts("table.cmp-table td.td0101 dl > dt")
    for t in dt0101[1:] if dt0101 else []:
        t = clean_text(t)
        if not t:
            continue
        if t.startswith("KOSPI") or t.startswith("KOSDAQ"):
            out["시장"] = t
        elif t.startswith("WICS"):
            out["WICS"] = t
        else:
            if "영문명" not in out:
                out["영문명"] = t

    # --- 2) td0301: EPS/BPS/PER/업종PER/PBR/현금배당수익률/결산 ---
    base_dl = "table.cmp-table td.td0301 dl"
    dt_sel = f"{base_dl} > dt"

    dt_texts = await browser.all_texts(dt_sel)  # dt 전체 텍스트(숫자 포함)
    if not dt_texts:
        return out

    # dt는 DOM 상에서 1..N 순서
    for i, raw_dt in enumerate(dt_texts, start=1):
        dt_text = clean_text(raw_dt)
        if not dt_text:
            continue

        num_sel = f"{base_dl} > dt:nth-child({i}) b.num"

        # 숫자 없는 라인: 예) "12월 결산"
        if not await browser.is_attached(num_sel):
            if "결산" in dt_text:
                out["결산"] = dt_text
            continue

        num_text = clean_text(await browser.text_content_first(num_sel))
        if not num_text:
            continue

        label = clean_text(dt_text.replace(num_text, "")).replace(":", "")
        if label:
            out[label] = to_number(num_text)

    return out
