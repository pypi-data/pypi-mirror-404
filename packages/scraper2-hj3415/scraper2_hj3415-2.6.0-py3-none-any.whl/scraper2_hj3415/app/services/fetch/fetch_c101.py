# scraper2_hj3415/app/usecases/fetch/fetch_c101.py
from __future__ import annotations

import asyncio
import random
from typing import Iterable

from logging_hj3415 import logger
from scraper2_hj3415.app.ports.browser.browser_factory_port import BrowserFactoryPort
from scraper2_hj3415.app.parsing.c101_parser import parse_c101_to_dict

from scraper2_hj3415.app.services.nfs_doc_builders import build_c101_doc_from_parsed
from scraper2_hj3415.app.domain.endpoint import EndpointKind
from scraper2_hj3415.app.domain.doc import NfsDoc
from scraper2_hj3415.app.domain.blocks import BLOCK_KEYS_BY_ENDPOINT


class FetchC101:
    def __init__(self, factory: BrowserFactoryPort):
        self.factory = factory

    async def _fetch_one(self, code: str, *, sleep_sec: float) -> NfsDoc | None:
        async with self.factory.lease() as browser:
            url = f"https://navercomp.wisereport.co.kr/v2/company/c1010001.aspx?cmp_cd={code}"
            await browser.goto_and_wait_for_stable(url, timeout_ms=10_000)

            if sleep_sec > 0:
                await asyncio.sleep(sleep_sec + random.uniform(0, 1.0))

            parsed = await parse_c101_to_dict(browser)

            logger.debug(f"parsed data: {parsed}")
            block_keys = BLOCK_KEYS_BY_ENDPOINT[EndpointKind.C101]
            if not parsed or all(not (parsed.get(str(bk)) or []) for bk in block_keys):
                logger.warning(
                    f"c101 fetch: parsed result empty; return None | code={code}"
                )
                return None

            doc = build_c101_doc_from_parsed(
                code=code, parsed=parsed, keep_empty_blocks=True
            )
            logger.debug(f"c101 doc: {doc}")
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
