# scraper2_hj3415/app/parsing/_normalize/table.py
from __future__ import annotations

from collections import Counter

import numpy as np
import pandas as pd
from .label import normalize_col_label, normalize_metric_label


def _dedupe_columns(cols: list[str]) -> list[str]:
    """
    정규화 후 중복 컬럼명이 생기면 자동으로 _2, _3 ... 붙여서 유니크하게 만든다.
    예) ["전년대비", "전년대비"] -> ["전년대비", "전년대비_2"]
    """
    seen: Counter[str] = Counter()
    out: list[str] = []
    for c in cols:
        c = c or ""
        seen[c] += 1
        if seen[c] == 1:
            out.append(c)
        else:
            out.append(f"{c}_{seen[c]}")
    return out


# -----------------------------
# 3) DataFrame 전체 정규화 + records 변환
# -----------------------------
def normalize_metrics_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    - 컬럼명 전체 정규화
    - '항목' 값 정규화
    - NaN -> None
    - 중복 컬럼명 자동 분리(_2/_3)
    """
    if df is None or df.empty:
        return df

    df = df.copy()

    # 컬럼명 정규화 + 중복 방지
    norm_cols = [normalize_col_label(c) for c in df.columns.astype(str).tolist()]
    df.columns = _dedupe_columns(norm_cols)

    # 항목 값 정규화
    if "항목" in df.columns:
        df["항목"] = df["항목"].map(normalize_metric_label)

    # NaN -> None
    df = df.replace({np.nan: None})
    return df
