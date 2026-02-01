# scraper2_hj3415/app/parsing/_normalize/text.py
from __future__ import annotations

from typing import Any

from common_hj3415.utils import clean_text


def normalize_text(x: object | None) -> str:
    """
    임의의 값을 문자열로 정규화한다.
    - None → ""
    - 문자열 표현 규칙(clean_text) 적용
    """
    s = "" if x is None else str(x)
    return clean_text(s)


_NUM_EMPTY = {"", "-", "N/A", "NA", "null", "None"}


def display_text(x: Any) -> str:
    """
    출력용 문자열로 정규화한다.
    - '-', 'N/A' 등 의미 없는 값은 제거
    """
    s = normalize_text(x)
    if not s or s in _NUM_EMPTY:
        return ""
    return s

