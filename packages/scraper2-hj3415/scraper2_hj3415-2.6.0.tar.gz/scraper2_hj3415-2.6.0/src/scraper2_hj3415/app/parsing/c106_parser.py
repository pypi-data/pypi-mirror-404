# scraper2_hj3415/app/parsing/c106_parser.py
from __future__ import annotations

from io import StringIO
import re
import numpy as np
import pandas as pd
from typing import Any

from common_hj3415.utils import clean_text
from scraper2_hj3415.app.ports.browser.browser_port import BrowserPort
from scraper2_hj3415.app.parsing._normalize.label import (
    normalize_metric_label,
    sanitize_label,
)
from logging_hj3415 import logger

_CODE_RE = re.compile(r"\b\d{6}\b")


async def parse_c106_header_codes(browser: BrowserPort) -> list[str]:
    """
    현재 페이지에서 '기업간비교자료' 헤더(회사명들)에서 종목코드(6자리)만 추출한다.
    (goto/sleep 없음)
    """
    selector = (
        'xpath=//caption[contains(normalize-space(.), "기업간비교자료")]'
        "/following-sibling::thead//th[not(@colspan)]"
    )
    await browser.wait_attached(selector)
    th_texts = await browser.all_texts(selector)

    codes: list[str] = []
    for i, t in enumerate(th_texts):
        text = (t or "").strip()
        if not text:
            continue
        m = _CODE_RE.search(text)
        if not m:
            continue
        codes.append(m.group(0))

    # 중복 제거(순서 유지)
    seen: set[str] = set()
    uniq: list[str] = []
    for c in codes:
        if c not in seen:
            seen.add(c)
            uniq.append(c)
    logger.debug(f"c106 header codes: {uniq}")
    return uniq


def html_table_to_df(html: str, codes: list[str]) -> pd.DataFrame:
    df = pd.read_html(StringIO(html), header=None)[0]
    if df is None or df.empty:
        return pd.DataFrame()

    df.columns = ["항목_group", "항목"] + codes
    df["항목_group"] = df["항목_group"].ffill()

    # 첫 두 줄 주가데이터 주입(기존 로직 유지)
    for i in range(min(2, len(df))):
        row = df.loc[i].tolist()
        new_row = ["주가데이터"] + row
        df.loc[i] = new_row[: len(df.columns)]

    df = df[df["항목"].notna()].reset_index(drop=True)
    df.loc[df["항목"].isin(["투자의견", "목표주가(원)"]), "항목_group"] = "기타지표"
    df = df[df["항목"] != "재무연월"].reset_index(drop=True)

    for col in df.columns[2:]:
        df[col] = df[col].replace("-", "0")
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["항목_group"] = df["항목_group"].astype("string").map(clean_text)
    df["항목"] = df["항목"].astype("string").map(clean_text)

    return df.replace({np.nan: None})


def df_to_c106_metric_list(df: pd.DataFrame) -> list[dict[str, Any]]:
    """
    C106 DataFrame -> records(list[dict])

    A안 적용:
    - 항목(key)은 normalize_c1034_item으로 강하게 정규화(괄호/별표 등 제거)
    - 항목_raw는 정규화 전(단 UI 노이즈만 제거된) 원라벨을 저장
    - 항목_group은 그대로 두되, 필요 없으면 caller에서 삭제하면 됨
    """
    if df is None or df.empty:
        return []

    df = df.copy()

    # raw 보존(정규화 전, UI 노이즈만 제거)
    raw = df["항목"].where(df["항목"].notna(), None)
    df["항목_raw"] = raw.map(
        lambda x: sanitize_label(str(x)) if x is not None else None
    )

    # 항목_group 컬럼들은 제거(있을 때만)
    drop_cols = [c for c in ("항목_group", "항목_group_raw") if c in df.columns]
    if drop_cols:
        df = df.drop(columns=drop_cols)

    # key 정규화(A안)
    df["항목"] = df["항목"].map(
        lambda x: normalize_metric_label(str(x)) if x is not None else ""
    )

    # 유효 행만
    df = df[df["항목"].astype(str).str.strip() != ""].reset_index(drop=True)

    # NaN -> None
    df = df.where(pd.notnull(df), None)

    return df.to_dict(orient="records")


async def parse_c106_current_table(
    browser: BrowserPort,
    *,
    columns: list[str],
    table_selector: str = "#cTB611",
    table_index: int = 0,
    timeout_ms: int = 10_000,
) -> list[dict[str, Any]]:
    """
    ✅ 현재 화면(이미 goto/대기 완료된 상태)에서 비교테이블만 파싱한다.
    """
    await browser.wait_table_nth_ready(
        table_selector, index=table_index, min_rows=3, timeout_ms=timeout_ms
    )
    html = await browser.outer_html_nth(table_selector, table_index)
    df = html_table_to_df(html, columns)
    return df_to_c106_metric_list(df)
