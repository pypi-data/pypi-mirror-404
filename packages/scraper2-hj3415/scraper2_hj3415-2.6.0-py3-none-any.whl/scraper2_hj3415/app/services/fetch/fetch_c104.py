# scraper2_hj3415/app/usecases/fetch/fetch_c104.py
from __future__ import annotations

import asyncio
import random
from typing import Iterable, Any

from logging_hj3415 import logger
from scraper2_hj3415.app.ports.browser.browser_factory_port import BrowserFactoryPort
from scraper2_hj3415.app.ports.site.wisereport_port import WiseReportPort
from scraper2_hj3415.app.adapters.site.wisereport_playwright import WiseReportPlaywright

from scraper2_hj3415.app.parsing.c104_parser import (
    parse_c104_current_table,
    TABLE_XPATH,
)
from scraper2_hj3415.app.services.nfs_doc_builders import build_metrics_doc_from_parsed
from scraper2_hj3415.app.domain.endpoint import EndpointKind
from scraper2_hj3415.app.domain.doc import NfsDoc
from scraper2_hj3415.app.domain.blocks import BLOCK_KEYS_BY_ENDPOINT


BTN_SETS: dict[str, list[tuple[str, str]]] = {
    "수익성y": [
        ("수익성", 'xpath=//*[ @id="val_tab1"]'),
        ("연간", 'xpath=//*[@id="frqTyp0"]'),
        ("검색", 'xpath=//*[@id="hfinGubun"]'),
    ],
    "성장성y": [
        ("성장성", 'xpath=//*[ @id="val_tab2"]'),
        ("연간", 'xpath=//*[@id="frqTyp0"]'),
        ("검색", 'xpath=//*[@id="hfinGubun"]'),
    ],
    "안정성y": [
        ("안정성", 'xpath=//*[ @id="val_tab3"]'),
        ("연간", 'xpath=//*[@id="frqTyp0"]'),
        ("검색", 'xpath=//*[@id="hfinGubun"]'),
    ],
    "활동성y": [
        ("활동성", 'xpath=//*[ @id="val_tab4"]'),
        ("연간", 'xpath=//*[@id="frqTyp0"]'),
        ("검색", 'xpath=//*[@id="hfinGubun"]'),
    ],
    "가치분석y": [
        ("가치분석연간", 'xpath=//*[@id="frqTyp0_2"]'),
        ("가치분석검색", 'xpath=//*[@id="hfinGubun2"]'),
    ],
    "수익성q": [
        ("수익성", 'xpath=//*[ @id="val_tab1"]'),
        ("분기", 'xpath=//*[@id="frqTyp1"]'),
        ("검색", 'xpath=//*[@id="hfinGubun"]'),
    ],
    "성장성q": [
        ("성장성", 'xpath=//*[ @id="val_tab2"]'),
        ("분기", 'xpath=//*[@id="frqTyp1"]'),
        ("검색", 'xpath=//*[@id="hfinGubun"]'),
    ],
    "안정성q": [
        ("안정성", 'xpath=//*[ @id="val_tab3"]'),
        ("분기", 'xpath=//*[@id="frqTyp1"]'),
        ("검색", 'xpath=//*[@id="hfinGubun"]'),
    ],
    "활동성q": [
        ("활동성", 'xpath=//*[ @id="val_tab4"]'),
        ("분기", 'xpath=//*[@id="frqTyp1"]'),
        ("검색", 'xpath=//*[@id="hfinGubun"]'),
    ],
    "가치분석q": [
        ("가치분석분기", 'xpath=//*[@id="frqTyp1_2"]'),
        ("가치분석검색", 'xpath=//*[@id="hfinGubun2"]'),
    ],
}


def _is_value_analysis(key: str) -> bool:
    return key.startswith("가치분석")


def _table_index_for_key(key: str) -> int:
    # ✅ 네 주석대로 가치분석만 1, 나머지 0
    return 1 if _is_value_analysis(key) else 0


class FetchC104:
    def __init__(self, factory: BrowserFactoryPort):
        self.factory = factory

    async def _fetch_one(self, code: str, *, sleep_sec: float) -> NfsDoc | None:
        async with self.factory.lease() as browser:
            wr: WiseReportPort = WiseReportPlaywright(browser)

            url = (
                "https://navercomp.wisereport.co.kr/v2/company/c1040001.aspx"
                f"?cn=&cmp_cd={code}"
            )
            await browser.goto_and_wait_for_stable(url, timeout_ms=10_000)

            if sleep_sec > 0:
                await asyncio.sleep(sleep_sec + random.uniform(0, 1.0))

            parsed: dict[str, list[dict[str, Any]]] = {}

            # ✅ table index별로 prev_text를 따로 들고가야 안정적
            prev_text_by_idx: dict[int, str | None] = {0: None, 1: None}

            # ✅ 최초 baseline 확보(둘 다 시도)
            for idx in (0, 1):
                try:
                    prev_text_by_idx[idx] = await browser.wait_table_text_changed(
                        TABLE_XPATH,
                        index=idx,
                        prev_text=None,
                        min_rows=5,
                        min_lines=50,
                        timeout_sec=10.0,
                    )
                except Exception:
                    prev_text_by_idx[idx] = None

            for key, steps in BTN_SETS.items():
                idx = _table_index_for_key(key)

                # ✅ 상태 전환(행동)
                await wr.click_steps(steps, jitter_sec=0.6)
                await wr.ensure_yearly_consensus_open_in_table_nth(
                    table_selector=TABLE_XPATH,
                    table_index=idx,
                )

                # ✅ 데이터 변경 대기(행동) - idx별로 추적
                prev_text_by_idx[idx] = await browser.wait_table_text_changed(
                    TABLE_XPATH,
                    index=idx,
                    prev_text=prev_text_by_idx[idx],
                    min_rows=5,
                    min_lines=50,
                    timeout_sec=12.0,
                )

                # ✅ 파싱은 “현재 화면의 idx 테이블 1개”만
                try:
                    parsed[key] = await parse_c104_current_table(
                        browser,
                        table_index=idx,
                    )
                except Exception:
                    parsed[key] = []

            logger.debug(f"parsed:\n{parsed}")

            block_keys = BLOCK_KEYS_BY_ENDPOINT[EndpointKind.C104]
            if not parsed or all(not (parsed.get(str(bk)) or []) for bk in block_keys):
                logger.warning(
                    f"c104 fetch: parsed result empty; return None | code={code}"
                )
                return None

            doc = build_metrics_doc_from_parsed(
                code=code,
                endpoint_kind=EndpointKind.C104,
                parsed=parsed,
                block_keys=block_keys,
                item_key="항목",
                raw_label_key="항목_raw",
                keep_empty_blocks=True,
            )
            logger.debug(f"c104 doc: {doc}")
            return doc

    async def execute(self, code: str, *, sleep_sec: float = 2.0) -> NfsDoc | None:
        return await self._fetch_one(code, sleep_sec=sleep_sec)

    async def execute_many(
        self,
        codes: Iterable[str],
        *,
        sleep_sec: float = 2.0,
    ) -> list[NfsDoc]:
        results = await asyncio.gather(
            *(self._fetch_one(c, sleep_sec=sleep_sec) for c in codes),
            return_exceptions=False,
        )
        return [r for r in results if r is not None]
