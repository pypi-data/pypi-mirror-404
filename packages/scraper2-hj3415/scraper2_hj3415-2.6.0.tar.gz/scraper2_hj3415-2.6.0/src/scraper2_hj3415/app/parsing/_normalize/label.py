# scraper2_hj3415/app/parsing/_normalize/label.py
from __future__ import annotations

import re
from typing import Any

from common_hj3415.utils import clean_text
from scraper2_hj3415.app.parsing._normalize.text import normalize_text

# -----------------------------
# 일반적인 라벨 정규화
# -----------------------------

UI_LABEL_NOISE = (
    "펼치기",
    "접기",
    "더보기",
)


def sanitize_label(x: Any) -> str:
    """
    raw label(항목_raw 포함)에서:
      - '펼치기' 같은 UI 텍스트 제거
      - 과도한 공백 정리
      - 양끝 공백 제거
    """
    s = normalize_text(x)

    # UI 노이즈 단어 제거
    for w in UI_LABEL_NOISE:
        s = s.replace(w, " ")

    return clean_text(s)


# -----------------------------
# metric 라벨 정규화
# -----------------------------
_BRACKET_PATTERN = re.compile(r"\[[^\]]*\]")  # [구K-IFRS] 등
_EXTRA_WORDS_PATTERN = re.compile(r"(펼치기|연간컨센서스보기|연간컨센서스닫기)")
_ALL_PAREN_PATTERN = re.compile(r"\([^)]*\)")  # ★ 모든 괄호 제거


def normalize_label_base(text: str | None) -> str:
    s = sanitize_label(text)
    s = _EXTRA_WORDS_PATTERN.sub("", s)
    s = _BRACKET_PATTERN.sub("", s)
    s = _ALL_PAREN_PATTERN.sub("", s)
    s = s.replace("*", "")
    return clean_text(s)


def normalize_metric_label(text: str | None) -> str:
    # "보유 지분 (%)" → "보유 지분"   (공백 유지)
    return normalize_label_base(text)


def normalize_key_label(text: str | None) -> str:
    # "보유 지분 (%)" → "보유지분"
    s = normalize_label_base(text)
    return s.replace(" ", "").replace("\xa0", "").replace("%", "").strip()


# -----------------------------
# 컬럼명 정규화
# -----------------------------
_COL_PAREN_PATTERN = re.compile(r"\((IFRS[^)]*|E|YoY|QoQ)[^)]*\)")
_COL_EXTRA_WORDS = re.compile(r"(연간컨센서스보기|연간컨센서스닫기)")
_COL_DOTNUM = re.compile(r"\.\d+$")  # pandas 중복 컬럼 suffix 제거용 (.1, .2 ...)


def normalize_col_label(col: str | None) -> str:
    """
    컬럼명 정규화
    예)
      "2024/12 (IFRS연결)  연간컨센서스보기" -> "2024/12"
      "2025/12(E) (IFRS연결)  연간컨센서스닫기" -> "2025/12"
      "전년대비 (YoY)" -> "전년대비"
      "전년대비 (YoY).1" -> "전년대비"  (중복은 후처리에서 _2/_3로 자동 분리)
    """
    s = normalize_text(col)
    # 1) pandas가 붙인 .1 같은 suffix 제거 (정규화 충돌은 후단에서 처리)
    s = _COL_DOTNUM.sub("", s)

    # 2) 컨센서스 문구 제거
    s = _COL_EXTRA_WORDS.sub("", s)

    # 3) 괄호 주석 제거: (IFRS...), (E), (YoY), (QoQ)
    s = _COL_PAREN_PATTERN.sub("", s)

    return clean_text(s)
