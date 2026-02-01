# scraper2_hj3415/app/parsing/c108_parser.py
from __future__ import annotations

import re
from html import unescape
from typing import Any
from common_hj3415.utils import clean_text
from scraper2_hj3415.app.ports.browser.browser_port import BrowserPort

_TAGS = re.compile(r"<[^>]+>")
_WS = re.compile(r"\s+")

_TD_ID_RE = re.compile(r"^td(\d+)$")   # td0, td1, ...
_C_ID_RE = re.compile(r"^c(\d+)$")     # c0, c1, ...


def _clean_text(x: Any) -> str:
    """
    경계/로깅/파싱 단계에서 Any를 안전하게 사람이 읽을 문자열로 만든다.
    - Any → str
    - html entity unescape
    - 이후 normalize_text 적용
    """
    if x is None:
        return ""
    s = unescape(str(x))   # ❗ x or "" 대신 None만 처리 (falsy 보존)
    return clean_text(s)


def _clean_html_to_text(html: str) -> str:
    s = unescape(html or "")
    s = s.replace("<br/>", "\n").replace("<br>", "\n").replace("<br />", "\n")
    s = _TAGS.sub("", s)
    s = s.replace("\r", "")
    lines = [ln.strip() for ln in s.split("\n")]
    lines = [ln for ln in lines if ln]
    return "\n".join(lines).strip()


_UI_LINES = {"요약정보닫기"}
_UI_PREFIXES = ("요약정보 :", "요약정보:")
_BULLET_RE = re.compile(r"^\s*▶\s*")
_MULTI_NL = re.compile(r"\n{3,}")


def _prettify_report_text(
    text: str,
    *,
    bullet: str = "- ",
) -> str:
    if not text:
        return ""

    lines = [ln.strip() for ln in text.split("\n")]
    out: list[str] = []

    for ln in lines:
        if not ln:
            continue

        # UI 잔재 제거 (prefix)
        for p in _UI_PREFIXES:
            if ln.startswith(p):
                ln = ln[len(p) :].strip()
                break
        if not ln:
            continue

        if ln in _UI_LINES:
            continue

        # 불릿 정리
        if _BULLET_RE.match(ln):
            ln = _BULLET_RE.sub(bullet, ln)

        out.append(ln)

    s = "\n".join(out)
    s = _MULTI_NL.sub("\n\n", s).strip()
    return s


def _parse_target_price(x: Any) -> int | None:
    s = _clean_text(x)
    if not s:
        return None
    s2 = re.sub(r"[^0-9]", "", s)
    if not s2:
        return None
    try:
        return int(s2)
    except Exception:
        return None


def _parse_pages(x: Any) -> int | None:
    s = _clean_text(x)
    m = re.search(r"(\d+)", s)
    return int(m.group(1)) if m else None


async def parse_c108_recent_reports_dom(
    browser: BrowserPort,
    *,
    table_selector: str = "#tableCmpDetail",
) -> list[dict[str, Any]]:
    """
    pandas(read_html) 없이 DOM 기반으로 안정적으로 추출.

    전제:
    - "정상 행"에는 td[id^='td'] 가 있고, 그 id가 tdN 형태다.
    - "상세 요약(숨김)"은 td[id='cN'] data-content로 붙어있다.
    - summary는 td[id='tdN'] data-content에, comment는 td[id='cN'] data-content에 들어있다.

    BrowserPort 요구 기능:
    - wait_attached(selector)
    - count_in_nth(scope_selector, scope_index, inner_selector) -> int
    - eval_in_nth_first(scope_selector, scope_index, inner_selector, expression) -> Any
      (이미 네가 추가해둔 형태 그대로 사용)
    """

    await browser.wait_attached(table_selector)

    # tbody tr 개수
    tr_count = await browser.count_in_nth(
        table_selector, scope_index=0, inner_selector="tbody tr"
    )
    if tr_count <= 0:
        return []

    out: list[dict[str, Any]] = []

    for tr_idx in range(tr_count):
        # row scope: table_selector >> tbody tr (nth=tr_idx)
        row_scope = f"{table_selector} >> tbody tr >> nth={tr_idx}"

        # 1) 이 행이 "정상 행"인지 판정: td[id^=td]가 있어야 함
        td_id = await browser.eval_in_nth_first(
            row_scope,
            scope_index=0,
            inner_selector="td[id^='td']",
            expression="el => el.id",
        )
        td_id = _clean_text(td_id)
        m = _TD_ID_RE.match(td_id)
        if not m:
            # 숨김 상세행(cN) 같은 건 스킵
            continue

        n = m.group(1)  # row_id
        # 2) 컬럼 텍스트 추출 (C108 테이블 구조에 맞게 td 순서 기준)
        #    보통: 1=일자, 2=제목, 3=작성자, 4=제공처, 5=투자의견, 6=목표가, 7=분량 ...
        date = _clean_text(
            await browser.eval_in_nth_first(
                row_scope,
                scope_index=0,
                inner_selector="td:nth-child(1)",
                expression="el => el.innerText",
            )
        )
        title = _clean_text(
            await browser.eval_in_nth_first(
                row_scope,
                scope_index=0,
                inner_selector="td:nth-child(2)",
                expression="el => el.innerText",
            )
        )

        # 최소 필터
        if not date or not title:
            continue

        authors = _clean_text(
            await browser.eval_in_nth_first(
                row_scope,
                scope_index=0,
                inner_selector="td:nth-child(3)",
                expression="el => el.innerText",
            )
        ) or None

        provider = _clean_text(
            await browser.eval_in_nth_first(
                row_scope,
                scope_index=0,
                inner_selector="td:nth-child(4)",
                expression="el => el.innerText",
            )
        ) or None

        rating = _clean_text(
            await browser.eval_in_nth_first(
                row_scope,
                scope_index=0,
                inner_selector="td:nth-child(5)",
                expression="el => el.innerText",
            )
        ) or None

        target_price_raw = await browser.eval_in_nth_first(
            row_scope,
            scope_index=0,
            inner_selector="td:nth-child(6)",
            expression="el => el.innerText",
        )
        target_price = _parse_target_price(target_price_raw)

        pages_raw = await browser.eval_in_nth_first(
            row_scope,
            scope_index=0,
            inner_selector="td:nth-child(7)",
            expression="el => el.innerText",
        )
        pages = _parse_pages(pages_raw)

        # 3) summary/comment: N으로 tdN / cN의 data-content를 직접 읽기
        #    (DOM에 존재하지만 display:none인 경우도 data-content는 읽을 수 있음)
        summary_html = await browser.eval_in_nth_first(
            table_selector,
            scope_index=0,
            inner_selector=f"td#td{n}",
            expression="el => el.getAttribute('data-content') || ''",
        )
        comment_html = await browser.eval_in_nth_first(
            table_selector,
            scope_index=0,
            inner_selector=f"td#c{n}",
            expression="el => el.getAttribute('data-content') || ''",
        )

        summary = _prettify_report_text(_clean_html_to_text(_clean_text(summary_html)))
        comment = _prettify_report_text(_clean_html_to_text(_clean_text(comment_html)))

        out.append(
            {
                "row_id": n,
                "date": date,
                "title": title,
                "authors": authors,
                "provider": provider,
                "rating": rating,
                "target_price": target_price,
                "pages": pages,
                "summary": summary or None,
                "comment": comment or None,
            }
        )

    return out


async def parse_c108_to_dict(browser: BrowserPort) -> dict[str, list[dict[str, Any]]]:
    return {"리포트": await parse_c108_recent_reports_dom(browser)}