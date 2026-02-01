# scraper2_hj3415/app/parsing/c101/major_shareholders.py
from __future__ import annotations

from typing import Any
from scraper2_hj3415.app.ports.browser.browser_port import BrowserPort
from scraper2_hj3415.app.parsing._normalize.text import normalize_text
from scraper2_hj3415.app.parsing._normalize.label import normalize_key_label
from scraper2_hj3415.app.parsing._normalize.values import to_int, to_float

def _pick_value_by_norm_key(row: dict[str, Any], candidates: list[str]) -> Any:
    # row의 키들을 정규화 맵으로 만든 뒤 후보를 정규화해서 조회
    norm_map: dict[str, str] = {
        normalize_key_label(k): k for k in row.keys()
    }
    for cand in candidates:
        rk = norm_map.get(normalize_key_label(cand))
        if rk is None:
            continue
        v = row.get(rk)
        # "키만 있고 값이 비어있는" 경우 다음 후보 탐색
        if v is None:
            continue
        if isinstance(v, str) and not v.strip():
            continue
        return v
    return None


async def parse_c101_major_shareholders(browser: BrowserPort) -> list[dict[str, Any]]:
    table_sel = "#cTB13"
    await browser.wait_attached(table_sel)

    records = await browser.table_records(table_sel, header=0)

    if not records:
        return []

    out: list[dict[str, Any]] = []
    for r in records:
        name = normalize_text(_pick_value_by_norm_key(r, ["주요주주", "주요주주명"]))
        if not name:
            continue

        shares_raw = _pick_value_by_norm_key(
            r, ["보유주식수(보통)", "보유주식수", "보유주식수(보통주)"]
        )
        ratio_raw = _pick_value_by_norm_key(r, ["보유지분(%)", "보유지분", "보유지분%"])

        out.append(
            {
                "주요주주": name,
                "보유주식수": to_int(shares_raw),  # 파싱 실패 시 None 가능
                "보유지분": to_float(ratio_raw),  # "0.91%"도 처리되게 파서 보장 필요
            }
        )

    return out
