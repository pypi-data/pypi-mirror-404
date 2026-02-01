from typing import Any, Sequence

from io import StringIO
import pandas as pd

from logging_hj3415 import logger
from scraper2_hj3415.app.parsing._normalize.table import normalize_metrics_df
from common_hj3415.utils import clean_text


def _flatten_col(col: Any) -> str:
    """
    pandas MultiIndex 컬럼(tuple)을 사람이 쓰기 좋은 단일 key로 변환한다.
    - ('재무년월','재무년월') 같은 중복은 하나로 축약
    - 단위 문자열 제거
    - '주재 무제표' 같은 깨진 라벨 보정
    """
    if isinstance(col, tuple):
        parts = [clean_text(p) for p in col if clean_text(p)]
        if not parts:
            s = ""
        elif len(parts) == 2 and parts[0] == parts[1]:
            s = parts[0]
        else:
            s = "_".join(parts)
    else:
        s = clean_text(col)

    s = (
        s.replace("(억원, %)", "")
        .replace("(원)", "")
        .replace("(배)", "")
        .replace("(%)", "")
        .strip()
    )
    s = s.replace("주재 무제표", "주재무제표")
    return clean_text(s)


def try_html_table_to_df(
    html: str, *, flatten_cols: bool = False, header: int | Sequence[int] = 0
) -> pd.DataFrame | None:
    try:
        dfs = pd.read_html(StringIO(html), header=header)
    except Exception as e:
        logger.exception("pd.read_html failed: {}", e)
        return None
    if not dfs:
        return None
    df = dfs[0]
    if df is None or df.empty:
        return None

    if flatten_cols:
        df = df.copy()
        df.columns = [_flatten_col(c) for c in df.columns]
    return df


def df_to_c1034_metric_list(df: pd.DataFrame) -> list[dict[str, Any]]:
    """
    C103 테이블 DataFrame -> 정규화된 records(list[dict])
    - 항목이 비면 제거
    - 항목_raw(정규화 전 원래 라벨) 보존
    """
    if df is None or df.empty:
        return []

    df = df.copy()

    # 정규화 전에 원래 항목 라벨 보존
    if "항목" in df.columns:
        df["항목_raw"] = (
            df["항목"]
            .where(df["항목"].notna(), None)
            .map(lambda x: str(x) if x is not None else None)
        )

    df = normalize_metrics_df(df)

    records: list[dict[str, Any]] = []
    for r in df.to_dict(orient="records"):
        item = r.get("항목")
        if not item:
            continue
        records.append(r)
    return records

