# scraper2/app/parsing/_sise_normalize.py
from __future__ import annotations

import re
from typing import Mapping

# 공통 구분자: 값/키 둘 다 여기로 쪼갬
_DEFAULT_SEP = "/"

_UNIT_REPLACEMENTS = {
    "Weeks": "주",
    "Week": "주",
    # 필요해지면 여기에 추가
    # "Days": "일",
    # "Months": "개월",
}


def _clean_token(s: str) -> str:
    # 괄호/공백 제거 + 중복 공백 정리
    s = s.strip()
    s = s.replace("(", " ").replace(")", " ")
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _compact_key(s: str) -> str:
    s = _clean_token(s)
    s = _replace_units(s)      # ✅ 여기서 Weeks → 주
    return s.replace(" ", "")

def _split_slash(s: str) -> list[str]:
    return [p.strip() for p in s.split(_DEFAULT_SEP)]

def _replace_units(s: str) -> str:
    for src, dst in _UNIT_REPLACEMENTS.items():
        s = s.replace(src, dst)
    return s


def _maybe_expand_pair_key_value(key: str, value: str) -> dict[str, str] | None:
    ks = _split_slash(key)
    vs = _split_slash(value)
    if len(ks) <= 1 or len(ks) != len(vs):
        return None

    out: dict[str, str] = {}

    # 1) 특수 케이스: "수익률 (1M/3M/6M/1Y)"
    first = _clean_token(ks[0])
    m = re.match(r"^(?P<prefix>.+?)\s+(?P<token>[0-9A-Za-z]+)$", first)
    if m:
        prefix = m.group("prefix").strip()
        token0 = m.group("token").strip()
        tokens = [token0] + [_clean_token(x) for x in ks[1:]]
        for tok, v in zip(tokens, vs):
            out[_compact_key(f"{prefix}{tok}")] = v
        return out

    # 2) 일반 케이스 + "prefix 전파" (52Weeks 최고/최저 같은 패턴)
    # 첫 토큰이 "52Weeks 최고"처럼 "prefix + label"이면,
    # 이후 토큰이 "최저"처럼 prefix가 생략된 경우 prefix를 붙여준다.
    first_tok = _clean_token(ks[0])
    m2 = re.match(r"^(?P<prefix>[0-9A-Za-z]+)\s+(?P<label>.+)$", first_tok)
    if m2:
        prefix = m2.group("prefix").strip()
        label0 = m2.group("label").strip()
        labels = [label0] + [_clean_token(x) for x in ks[1:]]
        for lab, v in zip(labels, vs):
            out[_compact_key(f"{prefix}{lab}")] = v
        return out

    # 3) 완전 일반: 그대로 매칭
    for k, v in zip(ks, vs):
        out[_compact_key(k)] = v
    return out


def normalize_sise_kv_map(src: Mapping[str, str]) -> dict[str, str]:
    """
    c101 시세 블록(dict[str,str])을 "정규화된 키 dict"로 변환.

    정규화 규칙:
    - key/value에 "/"가 있고 길이가 맞으면 분해해 여러 항목으로 확장
      예) "거래량/거래대금" -> "거래량", "거래대금"
      예) "52Weeks 최고/최저" -> "52Weeks최고", "52Weeks최저"
      예) "수익률 (1M/3M/6M/1Y)" -> "수익률1M", "수익률3M", ...
    - 나머지는 key의 공백 제거 정도만 적용해서 유지
    """
    out: dict[str, str] = {}

    for k, v in src.items():
        k = k.strip()
        v = v.strip()

        expanded = _maybe_expand_pair_key_value(k, v)
        if expanded:
            out.update(expanded)
            continue

        out[_compact_key(k)] = v

    return out