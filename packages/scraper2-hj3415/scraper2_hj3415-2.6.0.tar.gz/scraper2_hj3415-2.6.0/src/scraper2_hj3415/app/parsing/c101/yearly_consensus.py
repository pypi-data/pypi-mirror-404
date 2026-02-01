# scraper2_hj3415/app/parsing/c101/yearly_consensus.py
from __future__ import annotations

from io import StringIO
import re
from typing import Any

import pandas as pd

from scraper2_hj3415.app.ports.browser.browser_port import BrowserPort
from scraper2_hj3415.app.parsing._normalize.values import to_float
from scraper2_hj3415.app.parsing._normalize.text import normalize_text
from common_hj3415.utils import clean_text
from logging_hj3415 import logger

_YEARLY_CONSENSUS_TABLE = "#cTB25"


# -----------------------------
# column / period normalize
# -----------------------------
_COL_UNIT_RE = re.compile(r"\([^)]*\)")  # (억원, %), (원), (배) ... 제거용
_PERIOD_RE = re.compile(r"^\s*(\d{4})\s*\(?([A-Za-z])?\)?\s*$")  # 2022(A), 2025(E)


def _flatten_col(col: Any) -> str:
    """
    pd.read_html(header=[0,1])로 생긴 MultiIndex 컬럼을 '매출액_금액' 같은 단일 키로 만든다.
    - ('매출액(억원, %)', '금액') -> '매출액_금액'
    - ('매출액(억원, %)', 'YoY') -> '매출액_YoY'
    - 단위 괄호 제거
    """
    if isinstance(col, tuple):
        parts = [clean_text(str(p)) for p in col if clean_text(str(p))]
        if len(parts) == 2 and parts[0] == parts[1]:
            s = parts[0]
        else:
            s = "_".join(parts) if parts else ""
    else:
        s = clean_text(str(col))

    # 단위 괄호 제거
    s = _COL_UNIT_RE.sub("", s)
    s = clean_text(s)

    # 컬럼 표기 깨짐 보정
    s = s.replace("주재 무제표", "주재무제표")

    # 공백 제거(키 안정화)
    s = s.replace(" ", "")
    return s


def _normalize_period(
    s: Any,
    *,
    keep_suffix: bool = False,
) -> str | None:
    """
    기간 문자열을 표준 period key로 정규화한다.

    - "2022(A)", "2026(E)", "2022" 등을 처리
    - 기본 정책: 연간 = YYYY/12
    """
    t = normalize_text(s)
    if not t:
        return None

    # 헤더 방어
    if t == "재무년월":
        return None

    # 이미 표준 포맷이면 그대로
    if re.fullmatch(r"\d{4}/\d{2}", t):
        return t

    m = _PERIOD_RE.match(t)
    if not m:
        return None

    year, suffix = m.groups()  # suffix: "A" | "E" | None

    if keep_suffix and suffix:
        return f"{year}{suffix}"

    return f"{year}/{12}"


def _normalize_metric_key(col_key: str) -> str:
    """
    최종 metric key를 사람이 쓰기 좋은 형태로 정리.
    """
    k = col_key

    # 매출액은 '금액'/'YoY'가 분리되어 있으니 명시적으로 이름을 고정
    if k.startswith("매출액_금액"):
        return "매출액"
    if k.startswith("매출액_YoY"):
        return "매출액YoY"

    # 나머지는 그대로(단위/공백은 _flatten_col에서 제거됨)
    # 예: "영업이익", "당기순이익", "EPS", "PER", "PBR", "ROE", "EV/EBITDA", "순부채비율"
    return k


def _html_to_df(html: str) -> pd.DataFrame | None:
    """
    yearly consensus 테이블은 2줄 헤더이므로 header=[0,1]로 읽고 flatten한다.
    """
    try:
        dfs = pd.read_html(StringIO(html), header=[0, 1])
    except Exception as e:
        logger.exception("pd.read_html failed: {}", e)
        return None
    if not dfs:
        return None
    df = dfs[0]
    if df is None or df.empty:
        return None

    df = df.copy()
    df.columns = [_flatten_col(c) for c in df.columns]
    return df


def _df_to_metric_map(df: pd.DataFrame) -> dict[str, dict[str, Any]]:
    """
    DataFrame(row: period, col: metric) -> {metric: {period: value}} 로 pivot
    """
    if df is None or df.empty:
        return {}

    # NaN -> None
    df = df.where(pd.notnull(df), None)

    # '재무년월' 컬럼 찾기(안정)
    # 보통 "재무년월"로 flatten 되지만, 혹시 깨지는 경우 대비
    period_col = None
    for c in df.columns:
        if "재무년월" == c or c.endswith("재무년월") or "재무년월" in c:
            period_col = c
            break
    if not period_col:
        logger.warning("[cTB25] period column not found")
        return {}

    out: dict[str, dict[str, Any]] = {}

    for _, row in df.iterrows():
        period = _normalize_period(row.get(period_col), keep_suffix=True)
        if not period:
            continue

        for col, raw_val in row.items():
            if col == period_col:
                continue
            # 주재무제표는 metric-map에서 제외(원하면 따로 meta로 빼도 됨)
            if "주재무제표" in str(col):
                continue

            metric = _normalize_metric_key(str(col))

            num = to_float(raw_val)
            val: Any = num if num is not None else (normalize_text(raw_val) or None)

            out.setdefault(metric, {})[period] = val

    return out


async def parse_c101_yearly_consensus_table(
    browser: BrowserPort,
) -> dict[str, dict[str, Any]]:
    """
    #cTB25 (3년 실적 + 2년 추정) 테이블을
    {metric: {period: value}} 형태로 반환한다.
    """
    await browser.wait_attached(_YEARLY_CONSENSUS_TABLE)
    await browser.wait_table_nth_ready(
        _YEARLY_CONSENSUS_TABLE,
        index=0,
        min_rows=5,
        timeout_ms=30_000,
        poll_ms=200,
    )

    html = await browser.outer_html_nth(_YEARLY_CONSENSUS_TABLE, 0)
    if not html or "<table" not in html:
        logger.warning("[cTB25] outerHTML invalid or empty")
        return {}

    df = _html_to_df(html)
    if df is None:
        logger.warning("[cTB25] df is empty/invalid")
        return {}

    return _df_to_metric_map(df)