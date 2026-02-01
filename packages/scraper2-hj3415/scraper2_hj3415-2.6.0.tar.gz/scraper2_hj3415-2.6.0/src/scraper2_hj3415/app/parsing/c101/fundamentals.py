# scraper2_hj3415/app/parsing/c101/fundamentals.py
from __future__ import annotations

import re
from typing import Any
from scraper2_hj3415.app.ports.browser.browser_port import BrowserPort
from common_hj3415.utils import clean_text
from scraper2_hj3415.app.parsing._normalize.text import normalize_text
from scraper2_hj3415.app.parsing._normalize.values import to_number_or_text

_FUNDAMENTALS_TABLE = "div.fund.fl_le table.gHead03"


def _normalize_period_key(s: str) -> str:
    """
    예)
      "2024/12(A)" -> "2024/12"
      "2025/12(E)" -> "2025/12"
      "2025/12"    -> "2025/12"
    """
    s = s.strip()
    # 뒤쪽 괄호 주석 제거: (A) (E) (P) 등
    s = re.sub(r"\([^)]*\)$", "", s).strip()
    return s

EXCLUDED_METRICS = {"회계기준"}

async def parse_c101_fundamentals_table(
    browser: BrowserPort,
) -> dict[str, dict[str, Any]]:
    """
    '펀더멘털 주요지표(실적/컨센서스)' 테이블을
    metric_key -> {period_key -> value} 형태로 반환한다.

    반환 예)
      {
        "PBR": {"2024/12": 13.62, "2025/12": None},
        "회계기준": {"2024/12": "연결", "2025/12": "연결"},
        ...
      }
    """
    await browser.wait_attached(_FUNDAMENTALS_TABLE)

    rows = await browser.table_records(_FUNDAMENTALS_TABLE, header=0)
    if not rows:
        return {}

    cleaned_rows: list[dict[str, Any]] = []
    for r in rows:
        rr: dict[str, Any] = {}
        for k, v in r.items():
            kk = clean_text(k)
            if not kk:
                continue
            rr[kk] = normalize_text(v) if kk == "주요지표" else to_number_or_text(v)

        if rr.get("주요지표"):
            cleaned_rows.append(rr)

    if not cleaned_rows:
        return {}

    # columns: 순서 보존 합치기
    seen: set[str] = set()
    columns: list[str] = []
    for rr in cleaned_rows:
        for kk in rr.keys():
            if kk not in seen:
                seen.add(kk)
                columns.append(kk)

    metric_col = "주요지표" if "주요지표" in columns else columns[0]
    raw_value_cols = [c for c in columns if c != metric_col]

    # period_cols 정규화(괄호 제거)
    # ⚠️ "2024/12(A)" / "2025/12" 같은 원본 컬럼명을 유지해야 rr.get(...)이 되므로
    #    (원본컬럼, 정규화컬럼) 페어로 들고 간다.
    col_pairs: list[tuple[str, str]] = [(c, _normalize_period_key(c)) for c in raw_value_cols]

    metrics: dict[str, dict[str, Any]] = {}

    for rr in cleaned_rows:
        name = rr.get(metric_col)
        if not name:
            continue

        metric_key = str(name).strip()
        if metric_key in EXCLUDED_METRICS:
            continue  # ⬅️ 여기서 제외

        bucket = metrics.setdefault(metric_key, {})
        for raw_c, norm_c in col_pairs:
            bucket[norm_c] = rr.get(raw_c)

    return metrics