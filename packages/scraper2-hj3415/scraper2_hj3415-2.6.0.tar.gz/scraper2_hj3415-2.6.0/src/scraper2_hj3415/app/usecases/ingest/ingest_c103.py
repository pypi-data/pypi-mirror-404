# scraper2_hj3415/app/usecases/ingest/ingest_c103.py
from __future__ import annotations

from datetime import datetime
from typing import Iterable, Optional, cast

from scraper2_hj3415.app.services.fetch.fetch_c103 import FetchC103
from scraper2_hj3415.app.ports.sinks.nfs_sink_port import NfsSinkPort
from common_hj3415.utils.time import utcnow

from scraper2_hj3415.app.domain.endpoint import EndpointKind
from scraper2_hj3415.app.domain.constants import get_block_keys
from scraper2_hj3415.app.domain.doc import NfsDoc
from scraper2_hj3415.app.domain.blocks import MetricsBlock

from contracts_hj3415.nfs.types import Endpoints

from contracts_hj3415.nfs.c103_dto import (
    C103DTO,
    C103Payload,
    C103Blocks,
    C103Labels,
    C103ValuesMap,
)

from logging_hj3415 import logger


endpoint_kind = EndpointKind.C103
endpoint: Endpoints = cast(Endpoints, endpoint_kind.value)


def _metricsblock_to_c103_metric_map(block: MetricsBlock) -> dict[str, C103ValuesMap]:
    """
    MetricsBlock(domain) -> dict[MetricKey, dict[CodeKey, Num]]
    - domain MetricSeries.values 가 이미 {code: num} 형태라면 그대로 dict로 고정시킴.
    """
    out: dict[str, C103ValuesMap] = {}
    for mk, series in block.metrics.items():
        out[mk] = dict(series.values)  # Mapping -> dict
    return out


def c103_doc_to_dto(*, doc: NfsDoc, asof: datetime) -> C103DTO:
    """
    NfsDoc(domain, endpoint=c103) -> C103DTO(contracts envelope)

    C103Payload 구조:
      {
        "blocks": {"손익계산서y": {metric: {code: num}}, "손익계산서q": {...}},
        "labels": {"손익계산서y": {metric: raw_label}, "손익계산서q": {...}}
      }

    정책:
      - blocks/labels는 항상 y/q 키를 가진다. (없으면 빈 dict)
      - doc.labels는 없을 수도 있으니 dict()로 안전 변환
    """
    # 1) 기본 골격은 항상 채운다 (규약 안정성)
    blocks: C103Blocks = {
        "손익계산서y": {},
        "손익계산서q": {},
        "재무상태표y": {},
        "재무상태표q": {},
        "현금흐름표y": {},
        "현금흐름표q": {},
    }
    labels: C103Labels = {
        "손익계산서y": {},
        "손익계산서q": {},
        "재무상태표y": {},
        "재무상태표q": {},
        "현금흐름표y": {},
        "현금흐름표q": {},
    }

    # 2) 도메인 블록키 순서/목록 기준으로 채움
    for bk in get_block_keys(endpoint_kind):
        bd = doc.blocks.get(bk)
        if bd is None:
            continue

        if not isinstance(bd, MetricsBlock):
            raise TypeError(
                f"c103 expects MetricsBlock, got {type(bd).__name__} | block_key={bk!r}"
            )

        metric_map = _metricsblock_to_c103_metric_map(bd)
        label_map = dict(doc.labels.get(bk, {}))  # 없으면 {}

        match bk:
            case "손익계산서y":
                blocks["손익계산서y"] = metric_map
                labels["손익계산서y"] = label_map
            case "손익계산서q":
                blocks["손익계산서q"] = metric_map
                labels["손익계산서q"] = label_map
            case "재무상태표y":
                blocks["재무상태표y"] = metric_map
                labels["재무상태표y"] = label_map
            case "재무상태표q":
                blocks["재무상태표q"] = metric_map
                labels["재무상태표q"] = label_map
            case "현금흐름표y":
                blocks["현금흐름표y"] = metric_map
                labels["현금흐름표y"] = label_map
            case "현금흐름표q":
                blocks["현금흐름표q"] = metric_map
                labels["현금흐름표q"] = label_map
            case _:
                raise ValueError(f"invalid c103 block key: {bk!r}")

    payload: C103Payload = cast(C103Payload, {"blocks": blocks, "labels": labels})

    # ⚠️ TypedDict는 런타임 검증이 아니라 타입체커용이므로,
    # C103Payload(**payload) 같은 생성은 불가능(=TypedDict는 호출 불가)
    return C103DTO(
        code=doc.code,
        asof=asof,
        endpoint=endpoint,
        payload=payload,  # 그대로 dict 주입
    )


class IngestC103:
    def __init__(self, fetch: FetchC103, sink: NfsSinkPort[C103DTO]):
        self.fetch = fetch
        self.sink = sink

    async def execute(
        self,
        code: str,
        *,
        sleep_sec: float = 2.0,
        asof: datetime | None = None,
    ) -> C103DTO:
        asof = asof or utcnow()

        doc = await self.fetch.execute(code, sleep_sec=sleep_sec)
        logger.debug(f"doc:\n{doc}")
        if doc is None:
            raise RuntimeError(f"c106 fetch returned None: code={code}")

        dto = c103_doc_to_dto(doc=doc, asof=asof)
        logger.debug(f"dto:\n{dto}")

        await self.sink.write(dto, endpoint=endpoint)
        return dto

    async def execute_many(
        self,
        codes: Iterable[str],
        *,
        sleep_sec: float = 2.0,
        asof: Optional[datetime] = None,
    ) -> list[C103DTO]:
        batch_asof = asof or utcnow()

        docs = await self.fetch.execute_many(codes, sleep_sec=sleep_sec)
        dtos = [c103_doc_to_dto(doc=d, asof=batch_asof) for d in docs]
        logger.debug(f"dtos:\n{dtos}")
        await self.sink.write_many(dtos, endpoint=endpoint)
        return dtos
