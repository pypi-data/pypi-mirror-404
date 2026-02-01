# scraper2_hj3415/app/parsing/_normalize/values.py
from __future__ import annotations
import re
from typing import Any
from scraper2_hj3415.app.parsing._normalize.text import normalize_text


def parse_numeric(
    x: Any,
    *,
    strip_units: bool = False,
    keep_text: bool = False,
) -> int | float | str | None:
    """
    문자열을 숫자로 파싱 시도한다.

    - strip_units=True:
        '원', '%', '억' 등 단위를 제거한 뒤 숫자 파싱
    - strip_units=False:
        순수 숫자만 파싱
    """
    s = normalize_text(x)
    if not s:
        return None

    t = s.replace(",", "")
    if strip_units:
        t = (
            t.replace("원", "")
             .replace("억원", "")
             .replace("억", "")
             .replace("%", "")
             .strip()
        )

    # 정수
    if re.fullmatch(r"-?\d+", t):
        return int(t)

    # 실수
    if re.fullmatch(r"-?\d+(\.\d+)?", t):
        return float(t)

    return s if keep_text else None


def to_number(x: Any) -> int | float | None:
    """숫자만 허용 (실패 시 None)"""
    return parse_numeric(x, strip_units=True, keep_text=False)

def to_number_or_text(x: Any) -> float | str | None:
    """숫자면 숫자, 아니면 텍스트"""
    return parse_numeric(x, strip_units=True, keep_text=True)

def to_num_or_text(x: Any) -> int | float | str | None:
    """범용 셀 정규화"""
    return parse_numeric(x, strip_units=False, keep_text=True)

def to_int(x: Any) -> int | None:
    v = parse_numeric(x, strip_units=True, keep_text=False)
    if isinstance(v, (int, float)):
        return int(v)
    return None

def to_float(x: Any) -> float | None:
    v = parse_numeric(x, strip_units=True, keep_text=False)
    if isinstance(v, (int, float)):
        return float(v)
    return None

