# scraper2_hj3415/app/usecases/fetch/fetch_c106.py
from __future__ import annotations

import asyncio
import random
from typing import Iterable, Any

from logging_hj3415 import logger
from scraper2_hj3415.app.ports.browser.browser_factory_port import BrowserFactoryPort
from scraper2_hj3415.app.parsing.c106_parser import (
    parse_c106_header_codes,
    parse_c106_current_table,
)
from scraper2_hj3415.app.services.nfs_doc_builders import build_metrics_doc_from_parsed
from scraper2_hj3415.app.domain.endpoint import EndpointKind
from scraper2_hj3415.app.domain.doc import NfsDoc
from scraper2_hj3415.app.domain.blocks import BLOCK_KEYS_BY_ENDPOINT


class FetchC106:
    def __init__(self, factory: BrowserFactoryPort):
        self.factory = factory

    async def _fetch_one(self, code: str, *, sleep_sec: float) -> NfsDoc | None:
        async with self.factory.lease() as browser:
            # 1) 헤더 코드 추출용(기준 페이지)
            url0 = (
                "https://navercomp.wisereport.co.kr/v2/company/c1060001.aspx"
                f"?cn=&cmp_cd={code}"
            )
            await browser.goto_and_wait_for_stable(url0, timeout_ms=10_000)

            if sleep_sec > 0:
                await asyncio.sleep(sleep_sec + random.uniform(0, 1.0))

            header_codes = await parse_c106_header_codes(browser)
            if not header_codes:
                logger.warning(f"c106 fetch: header codes empty; code={code}")
                return None

            base_url = (
                "https://navercomp.wisereport.co.kr/v2/company/cF6002.aspx"
                f"?cmp_cd={code}&finGubun=MAIN&sec_cd=FG000&frq="
            )

            parsed: dict[str, list[dict[str, Any]]] = {}

            for frq in ("q", "y"):
                url = base_url + frq
                await browser.goto_and_wait_for_stable(url, timeout_ms=10_000)

                # 기존 지터 유지(필요하면 정책화)
                await asyncio.sleep(0.5 + random.uniform(0, 0.3))

                parsed[frq] = await parse_c106_current_table(
                    browser,
                    columns=header_codes,
                    table_selector="#cTB611",
                    table_index=0,
                    timeout_ms=10_000,
                )

            logger.debug(f"parsed:\n{parsed}")

            block_keys = BLOCK_KEYS_BY_ENDPOINT[EndpointKind.C106]
            if not parsed or all(not (parsed.get(str(bk)) or []) for bk in block_keys):
                logger.warning(f"c106 fetch: parsed result empty; return None | code={code}")
                return None

            doc = build_metrics_doc_from_parsed(
                code=code,
                endpoint_kind=EndpointKind.C106,
                parsed=parsed,
                block_keys=block_keys,
                item_key="항목",
                raw_label_key="항목_raw",
                keep_empty_blocks=True,
            )
            logger.debug(f"c106 doc: {doc}")
            return doc

    async def execute(self, code: str, *, sleep_sec: float = 2.0) -> NfsDoc | None:
        return await self._fetch_one(code, sleep_sec=sleep_sec)

    async def execute_many(self, codes: Iterable[str], *, sleep_sec: float = 2.0) -> list[NfsDoc]:
        results = await asyncio.gather(
            *(self._fetch_one(c, sleep_sec=sleep_sec) for c in codes),
            return_exceptions=False,
        )
        return [r for r in results if r is not None]