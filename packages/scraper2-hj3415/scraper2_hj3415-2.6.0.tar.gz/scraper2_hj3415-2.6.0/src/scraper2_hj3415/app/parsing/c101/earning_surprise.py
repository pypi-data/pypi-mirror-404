from __future__ import annotations

import re
from typing import Any
from scraper2_hj3415.app.ports.browser.browser_port import BrowserPort
from common_hj3415.utils import clean_text

_EARNING_SURPRISE_TABLE = "#earning_list"

def _strip_bullets_commas(s: str) -> str:
    """
    "●  120,064.0" / "101,922.8" 같은 텍스트에서 숫자 파싱을 방해하는 것 제거.
    """
    s = clean_text(s)
    s = s.replace(",", "")
    s = s.replace("●", "")
    s = s.replace("○", "")
    s = s.replace("▲", "")
    s = s.replace("▼", "")
    return clean_text(s)


def _to_number_like(x: Any) -> Any:
    """
    숫자면 float/int로, 아니면 문자열 그대로.
    """
    if x is None:
        return None
    if isinstance(x, (int, float)):
        return x
    s = _strip_bullets_commas(str(x))
    if not s:
        return None

    # 숫자 패턴이면 숫자로
    #  - "65.00" "209.17" "-123.4"
    if re.fullmatch(r"[-+]?\d+(\.\d+)?", s):
        # 정수면 int 유지하고 싶으면 여기서 분기 가능
        try:
            f = float(s)
            # "65.0" 같이 소수점 .0이면 int로 바꿀지 정책 선택
            return f
        except Exception:
            return s

    return s


def _norm_item_label(item: str) -> str:
    """
    item(th 텍스트) 정규화:
    - "전분기대비보기 전년동기대비" -> "전년동기대비"
    - "Surprise" 등은 그대로
    """
    t = clean_text(item)

    # 버튼 텍스트가 섞이는 케이스: "전분기대비보기 전년동기대비"
    if ("전분기대비" in t) and ("전년동기대비" in t):
        return "전년동기대비"
    if "전분기대비" in t:
        return "전분기대비"
    if "전년동기대비" in t:
        return "전년동기대비"
    if "컨센서스" in t:
        return "컨센서스"
    if "잠정치" in t:
        return "잠정치"
    if "Surprise" in t or "SURPRISE" in t or "surprise" in t:
        return "Surprise"

    return t


async def _row_cells_texts(
    browser: BrowserPort,
    *,
    row_sel: str,
) -> list[str]:
    """
    tbody의 특정 tr에서 th/td 텍스트를 왼쪽부터 순서대로 모두 가져온다.
    """
    # th,td 전체 개수
    n = await browser.count_in_nth(
        _EARNING_SURPRISE_TABLE,
        scope_index=0,
        inner_selector=f"{row_sel} th, {row_sel} td",
    )

    out: list[str] = []
    for j in range(n):
        txt = await browser.inner_text_in_nth(
            _EARNING_SURPRISE_TABLE,
            scope_index=0,
            inner_selector=f"{row_sel} th, {row_sel} td",
            inner_index=j,
        )
        out.append(clean_text(txt))
    return out


async def parse_c101_earnings_surprise_table(
    browser: BrowserPort,
    *,
    debug_rows: bool = False,
) -> dict[str, Any]:
    """
    earning_list HTML 구조(제공된 원본)에 맞춘 안정 파서.

    반환:
      {
        "periods": [...],
        "metrics": { section: { item: {period: value} } },
        "meta": {...},
        ...(debug_rows면 "rows": raw_cells_rows)
      }
    """
    await browser.wait_attached(_EARNING_SURPRISE_TABLE)

    row_cnt = await browser.count_in_nth(
        _EARNING_SURPRISE_TABLE,
        scope_index=0,
        inner_selector="tbody tr",
    )
    if not row_cnt:
        out = {"periods": [], "metrics": {}, "meta": {}}
        if debug_rows:
            out["rows"] = []
        return out

    raw_cells_rows: list[list[str]] = []

    periods: list[str] = []
    period_count = 0

    metrics: dict[str, dict[str, dict[str, Any]]] = {}
    meta: dict[str, dict[str, Any]] = {}

    current_section: str | None = None

    for i in range(1, row_cnt + 1):  # nth-child 1-based
        row_sel = f"tbody tr:nth-child({i})"
        cells = await _row_cells_texts(browser, row_sel=row_sel)
        raw_cells_rows.append(cells)

        if not cells:
            continue

        joined = " ".join([c for c in cells if c])

        # 1) periods 추출: "재무연월" 헤더 row
        # HTML: <th colspan="2">재무연월</th> + <th>2025/09</th> + <th>2025/12</th>
        if ("재무연월" in joined) and not periods:
            # cells 예: ["재무연월", "2025/09", "2025/12"] 또는 table 구조에 따라 3~4개
            # 여기서는 "YYYY/NN" 패턴만 뽑는 게 가장 안전함
            periods = [c for c in cells if re.fullmatch(r"\d{4}/\d{2}", c)]
            period_count = len(periods)
            continue

        # periods 없으면 본문 해석 불가
        if not periods:
            continue

        # 2) meta row: "잠정치발표(예정)일/회계기준"
        if "잠정치발표(예정)일/회계기준" in joined:
            # 보통 cells: ["잠정치발표(예정)일/회계기준", "2025/10/14(연결)", "2026/01/08(연결)"]
            vals = [c for c in cells if c and "잠정치발표" not in c]
            vals = vals[-period_count:] if period_count else vals
            meta["잠정치발표(예정)일/회계기준"] = {
                periods[idx]: vals[idx] if idx < len(vals) else None
                for idx in range(period_count)
            }
            continue

        # 3) 본문 row 정규화: 항상 [section, item, v1, v2, ...] 로 맞추기
        # HTML 케이스:
        #  - 섹션 시작 행(영업이익/당기순이익): cells = ["영업이익", "컨센서스", v1, v2]
        #  - rowspan 내부 다음 행:             cells = ["잠정치", v1, v2]  (section 없음 → 왼쪽 패딩 필요)
        #  - ext0 행(전분기대비):              cells = ["", "전분기대비", v1, v2]  (첫 칸 빈 th)
        #
        # period_count가 2라면, 정상형은 길이 2 + period_count = 4
        want_len = 2 + period_count

        norm = cells[:]
        if len(norm) == want_len - 1:
            # section th가 빠진 케이스: ["잠정치", v1, v2] -> ["", "잠정치", v1, v2]
            norm = [""] + norm
        elif len(norm) < want_len:
            # 애매한 경우: 오른쪽을 None으로 채움
            norm = ([""] * (want_len - len(norm))) + norm
            norm = norm[-want_len:]

        section_cell = clean_text(norm[0])
        item_cell = clean_text(norm[1])
        value_cells = norm[2 : 2 + period_count]

        # section 갱신
        if section_cell:
            current_section = section_cell
            metrics.setdefault(current_section, {})
        if not current_section:
            # 섹션이 한 번도 잡히지 않은 상태면 skip
            continue

        item = _norm_item_label(item_cell)
        if not item:
            continue

        # 값 매핑
        bucket = metrics[current_section].setdefault(item, {})
        for idx, p in enumerate(periods):
            raw_v = value_cells[idx] if idx < len(value_cells) else None
            bucket[p] = _to_number_like(raw_v)

    out: dict[str, Any] = {"periods": periods, "metrics": metrics, "meta": meta}
    if debug_rows:
        out["rows"] = raw_cells_rows
    return out