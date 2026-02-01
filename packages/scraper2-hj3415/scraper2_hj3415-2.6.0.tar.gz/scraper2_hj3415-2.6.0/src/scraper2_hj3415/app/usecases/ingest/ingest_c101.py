# scraper2_hj3415/app/usecases/ingest/ingest_c101.py
from __future__ import annotations

from datetime import datetime
from typing import Iterable, Optional, Any, cast

from scraper2_hj3415.app.services.fetch.fetch_c101 import FetchC101
from scraper2_hj3415.app.ports.sinks.nfs_sink_port import NfsSinkPort
from common_hj3415.utils.time import utcnow

from scraper2_hj3415.app.domain.endpoint import EndpointKind
from scraper2_hj3415.app.domain.constants import get_block_keys
from scraper2_hj3415.app.domain.doc import NfsDoc
from scraper2_hj3415.app.domain.blocks import KvBlock, RecordsBlock, MetricsBlock

from contracts_hj3415.nfs.types import Endpoints
from contracts_hj3415.nfs.c101_dto import C101DTO, C101Payload, C101Blocks

from logging_hj3415 import logger

endpoint_kind = EndpointKind.C101
endpoint: Endpoints = cast(Endpoints, endpoint_kind.value)


def _unwrap_c101_block(block: Any) -> Any:
    """
    domain BlockData -> DTO로 들어갈 순수 python 구조(dict/list/...)
    - C101은 KvBlock/RecordsBlock 위주
    - (혹시 MetricsBlock이 섞여도 안전하게 처리)
    """
    if isinstance(block, KvBlock):
        return dict(block.values)

    if isinstance(block, RecordsBlock):
        # rows: Sequence[Record] -> list[dict]
        return [dict(r) for r in block.rows]

    if isinstance(block, MetricsBlock):
        # C101에서 MetricsBlock 쓸 일은 거의 없겠지만, 안전망
        # metrics: Mapping[MetricKey, MetricSeries(values: Mapping[Period, Num])]
        out: dict[str, dict[str, Any]] = {}
        for mk, series in block.metrics.items():
            out[str(mk)] = dict(series.values)
        return out

    # 이미 dict/list 등으로 들어오는 케이스도 방어
    return block


def c101_doc_to_dto(*, doc: NfsDoc, asof: datetime) -> C101DTO:
    """
    NfsDoc(domain) -> C101DTO(contracts)

    규칙:
      - C101은 labels를 비우는 것이 정상 (하지만 payload에는 항상 존재)
      - blocks는 endpoint block_keys 순서대로 채우되, 각 블록은 BlockData를 언래핑해서 넣는다.
    """
    blocks: dict[str, Any] = {}
    labels: dict[str, dict[str, str]] = {}

    for bk in get_block_keys(endpoint_kind):
        block = doc.blocks.get(bk)
        blocks[str(bk)] = _unwrap_c101_block(block) if block is not None else {}

        # C101은 labels 항상 empty
        labels[str(bk)] = {}

    payload: C101Payload = cast(C101Payload, {"blocks": cast(C101Blocks, blocks), "labels": labels})

    return C101DTO(
        code=doc.code,
        asof=asof,
        endpoint=endpoint,
        payload=payload,
    )


class IngestC101:
    def __init__(self, fetch: FetchC101, sink: NfsSinkPort[C101DTO]):
        self.fetch = fetch
        self.sink = sink

    async def execute(
        self, code: str, *, sleep_sec: float = 2.0, asof: datetime | None = None
    ) -> C101DTO:
        asof = asof or utcnow()
        doc = await self.fetch.execute(code, sleep_sec=sleep_sec)
        logger.debug(f"doc:\n{doc}")
        if doc is None:
            raise RuntimeError(f"c101 fetch returned None: code={code}")

        dto = c101_doc_to_dto(doc=doc, asof=asof)
        logger.debug(f"dto:\n{dto}")

        await self.sink.write(dto, endpoint=endpoint)
        return dto

    async def execute_many(
        self,
        codes: Iterable[str],
        *,
        sleep_sec: float = 2.0,
        asof: Optional[datetime] = None,
    ) -> list[C101DTO]:
        batch_asof = asof or utcnow()

        docs = await self.fetch.execute_many(codes, sleep_sec=sleep_sec)
        dtos = [c101_doc_to_dto(doc=d, asof=batch_asof) for d in docs]
        logger.debug(f"dtos:\n{dtos}")
        await self.sink.write_many(dtos, endpoint=endpoint)
        return dtos
