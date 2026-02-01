# scraper2_hj3415/app/usecases/fetch/fetch_c103.py
from __future__ import annotations

import asyncio
import random
from typing import Iterable, Any

from logging_hj3415 import logger
from scraper2_hj3415.app.ports.browser.browser_factory_port import BrowserFactoryPort
from scraper2_hj3415.app.ports.site.wisereport_port import WiseReportPort

from scraper2_hj3415.app.adapters.site.wisereport_playwright import WiseReportPlaywright
from scraper2_hj3415.app.parsing.c103_parser import parse_c103_current_table
from scraper2_hj3415.app.services.nfs_doc_builders import build_metrics_doc_from_parsed

from scraper2_hj3415.app.domain.endpoint import EndpointKind
from scraper2_hj3415.app.domain.blocks import BLOCK_KEYS_BY_ENDPOINT
from scraper2_hj3415.app.domain.doc import NfsDoc

BTN_SETS: dict[str, list[tuple[str, str]]] = {
    "손익계산서y": [
        ("손익계산서", 'xpath=//*[@id="rpt_tab1"]'),
        ("연간", 'xpath=//*[@id="frqTyp0"]'),
        ("검색", 'xpath=//*[@id="hfinGubun"]'),
    ],
    "재무상태표y": [
        ("재무상태표", 'xpath=//*[@id="rpt_tab2"]'),
        ("연간", 'xpath=//*[@id="frqTyp0"]'),
        ("검색", 'xpath=//*[@id="hfinGubun"]'),
    ],
    "현금흐름표y": [
        ("현금흐름표", 'xpath=//*[@id="rpt_tab3"]'),
        ("연간", 'xpath=//*[@id="frqTyp0"]'),
        ("검색", 'xpath=//*[@id="hfinGubun"]'),
    ],
    "손익계산서q": [
        ("손익계산서", 'xpath=//*[@id="rpt_tab1"]'),
        ("분기", 'xpath=//*[@id="frqTyp1"]'),
        ("검색", 'xpath=//*[@id="hfinGubun"]'),
    ],
    "재무상태표q": [
        ("재무상태표", 'xpath=//*[@id="rpt_tab2"]'),
        ("분기", 'xpath=//*[@id="frqTyp1"]'),
        ("검색", 'xpath=//*[@id="hfinGubun"]'),
    ],
    "현금흐름표q": [
        ("현금흐름표", 'xpath=//*[@id="rpt_tab3"]'),
        ("분기", 'xpath=//*[@id="frqTyp1"]'),
        ("검색", 'xpath=//*[@id="hfinGubun"]'),
    ],
}


class FetchC103:
    def __init__(self, factory: BrowserFactoryPort):
        self.factory = factory

    async def _fetch_one(self, code: str, *, sleep_sec: float) -> NfsDoc | None:
        async with self.factory.lease() as browser:
            wr: WiseReportPort = WiseReportPlaywright(browser)

            url = (
                "https://navercomp.wisereport.co.kr/v2/company/c1030001.aspx"
                f"?cn=&cmp_cd={code}"
            )
            await browser.goto_and_wait_for_stable(url, timeout_ms=10_000)

            if sleep_sec > 0:
                await asyncio.sleep(sleep_sec + random.uniform(0, 1.0))

            parsed: dict[str, list[dict[str, Any]]] = {}
            prev_text: str | None = None

            # 최초 기준 텍스트 확보(없어도 동작하게)
            prev_text = await browser.wait_table_text_changed(
                "xpath=//div[@id='wrapper']//div//table",
                index=2,
                prev_text=None,
                min_rows=5,
                min_lines=50,
                timeout_sec=10.0,
            )

            for key, steps in BTN_SETS.items():
                # ✅ 상태 전환 (행동)
                await wr.click_steps(steps, jitter_sec=0.6)  # 포트/어댑터로 이동 권장
                await wr.ensure_yearly_consensus_open_in_table_nth(
                    table_selector="xpath=//div[@id='wrapper']//div//table",
                    table_index=2,
                )

                # ✅ 데이터 변경 대기 (행동)
                prev_text = await browser.wait_table_text_changed(
                    "xpath=//div[@id='wrapper']//div//table",
                    index=2,
                    prev_text=prev_text,
                    min_rows=5,
                    min_lines=50,
                    timeout_sec=12.0,
                )

                # ✅ 파싱은 “현재 화면 테이블”만
                try:
                    parsed[key] = await parse_c103_current_table(browser)
                except Exception:
                    parsed[key] = []

            block_keys = BLOCK_KEYS_BY_ENDPOINT[EndpointKind.C103]
            if not parsed or all(not (parsed.get(str(bk)) or []) for bk in block_keys):
                logger.warning(
                    f"c103 fetch: parsed result empty; return None | code={code}"
                )
                return None

            doc = build_metrics_doc_from_parsed(
                code=code,
                endpoint_kind=EndpointKind.C103,
                parsed=parsed,
                block_keys=block_keys,
                item_key="항목",
                raw_label_key="항목_raw",
                keep_empty_blocks=True,
            )
            return doc

    async def execute(self, code: str, *, sleep_sec: float = 2.0) -> NfsDoc | None:
        return await self._fetch_one(code, sleep_sec=sleep_sec)

    async def execute_many(
        self, codes: Iterable[str], *, sleep_sec: float = 2.0
    ) -> list[NfsDoc]:
        results = await asyncio.gather(
            *(self._fetch_one(c, sleep_sec=sleep_sec) for c in codes)
        )
        return [r for r in results if r is not None]
