# scraper2_hj3415/app/usecases/ingest/ingest_c106.py
from __future__ import annotations

from datetime import datetime
from typing import Iterable, Optional, cast

from scraper2_hj3415.app.services.fetch.fetch_c106 import FetchC106
from scraper2_hj3415.app.ports.sinks.nfs_sink_port import NfsSinkPort
from common_hj3415.utils.time import utcnow

from scraper2_hj3415.app.domain.endpoint import EndpointKind
from scraper2_hj3415.app.domain.constants import get_block_keys
from scraper2_hj3415.app.domain.doc import NfsDoc
from scraper2_hj3415.app.domain.blocks import MetricsBlock

from contracts_hj3415.nfs.types import Endpoints

from contracts_hj3415.nfs.c106_dto import (
    C106DTO,
    C106Payload,
    C106Blocks,
    C106Labels,
    C106ValuesMap,
)

from logging_hj3415 import logger


endpoint_kind = EndpointKind.C106
endpoint: Endpoints = cast(Endpoints, endpoint_kind.value)


def _metricsblock_to_c106_metric_map(block: MetricsBlock) -> dict[str, C106ValuesMap]:
    """
    MetricsBlock(domain) -> dict[MetricKey, dict[CodeKey, Num]]
    - domain MetricSeries.values 가 이미 {code: num} 형태라면 그대로 dict로 고정시킴.
    """
    out: dict[str, C106ValuesMap] = {}
    for mk, series in block.metrics.items():
        out[mk] = dict(series.values)  # Mapping -> dict
    return out


def c106_doc_to_dto(*, doc: NfsDoc, asof: datetime) -> C106DTO:
    """
    NfsDoc(domain, endpoint=c106) -> C106DTO(contracts envelope)

    C106Payload 구조:
      {
        "blocks": {"y": {metric: {code: num}}, "q": {...}},
        "labels": {"y": {metric: raw_label}, "q": {...}}
      }

    정책:
      - blocks/labels는 항상 y/q 키를 가진다. (없으면 빈 dict)
      - doc.labels는 없을 수도 있으니 dict()로 안전 변환
    """
    # 1) 기본 골격은 항상 채운다 (규약 안정성)
    blocks: C106Blocks = {"y": {}, "q": {}}
    labels: C106Labels = {"y": {}, "q": {}}

    # 2) 도메인 블록키 순서/목록 기준으로 채움
    for bk in get_block_keys(endpoint_kind):
        bd = doc.blocks.get(bk)
        if bd is None:
            continue

        if not isinstance(bd, MetricsBlock):
            raise TypeError(
                f"c106 expects MetricsBlock, got {type(bd).__name__} | block_key={bk!r}"
            )

        metric_map = _metricsblock_to_c106_metric_map(bd)
        label_map = dict(doc.labels.get(bk, {}))  # 없으면 {}

        match bk:
            case "y":
                blocks["y"] = metric_map
                labels["y"] = label_map
            case "q":
                blocks["q"] = metric_map
                labels["q"] = label_map
            case _:
                raise ValueError(f"invalid c106 block key: {bk!r}")

    payload: C106Payload = cast(C106Payload, {"blocks": blocks, "labels": labels})

    # ⚠️ TypedDict는 런타임 검증이 아니라 타입체커용이므로,
    # C106Payload(**payload) 같은 생성은 불가능(=TypedDict는 호출 불가)
    return C106DTO(
        code=doc.code,
        asof=asof,
        endpoint=endpoint,
        payload=payload,  # 그대로 dict 주입
    )


class IngestC106:
    def __init__(self, fetch: FetchC106, sink: NfsSinkPort[C106DTO]):
        self.fetch = fetch
        self.sink = sink

    async def execute(
        self,
        code: str,
        *,
        sleep_sec: float = 2.0,
        asof: datetime | None = None,
    ) -> C106DTO:
        asof = asof or utcnow()

        doc = await self.fetch.execute(code, sleep_sec=sleep_sec)
        logger.debug(f"doc:\n{doc}")
        if doc is None:
            raise RuntimeError(f"c106 fetch returned None: code={code}")

        dto = c106_doc_to_dto(doc=doc, asof=asof)
        logger.debug(f"dto:\n{dto}")

        await self.sink.write(dto, endpoint=endpoint)
        return dto

    async def execute_many(
        self,
        codes: Iterable[str],
        *,
        sleep_sec: float = 2.0,
        asof: Optional[datetime] = None,
    ) -> list[C106DTO]:
        batch_asof = asof or utcnow()

        docs = await self.fetch.execute_many(codes, sleep_sec=sleep_sec)
        dtos = [c106_doc_to_dto(doc=d, asof=batch_asof) for d in docs]
        logger.debug(f"dtos:\n{dtos}")
        await self.sink.write_many(dtos, endpoint=endpoint)
        return dtos
