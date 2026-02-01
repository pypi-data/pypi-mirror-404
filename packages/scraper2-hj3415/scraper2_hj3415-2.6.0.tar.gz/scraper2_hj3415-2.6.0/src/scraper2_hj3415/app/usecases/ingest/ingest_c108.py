# scraper2_hj3415/app/usecases/ingest/ingest_c108.py
from __future__ import annotations

from datetime import datetime
from typing import Iterable, Optional, cast

from scraper2_hj3415.app.services.fetch.fetch_c108 import FetchC108
from scraper2_hj3415.app.ports.sinks.nfs_sink_port import NfsSinkPort
from common_hj3415.utils.time import utcnow

from scraper2_hj3415.app.domain.endpoint import EndpointKind
from scraper2_hj3415.app.domain.constants import get_block_keys
from scraper2_hj3415.app.domain.doc import NfsDoc
from scraper2_hj3415.app.domain.blocks import RecordsBlock

from contracts_hj3415.nfs.types import Endpoints

from contracts_hj3415.nfs.c108_dto import C108DTO, C108Payload, C108Blocks

from logging_hj3415 import logger

endpoint_kind = EndpointKind.C108
endpoint: Endpoints = cast(Endpoints, endpoint_kind.value)


def _to_list_of_dict(rows: object) -> list[dict]:
    """
    RecordsBlock.rows(Sequence[Mapping]) -> list[dict]
    - sink/serialization 안전하게 dict로 강제
    """
    if not rows:
        return []
    out: list[dict] = []
    if isinstance(rows, list):
        for r in rows:
            if isinstance(r, dict):
                out.append(r)
            else:
                out.append(dict(r))  # Mapping이면 dict() 가능
        return out

    # Sequence[Mapping] 일반 케이스
    try:
        for r in rows:  # type: ignore[assignment]
            out.append(dict(r))  # Mapping 가정
    except Exception:
        return []
    return out


def c108_doc_to_dto(*, doc: NfsDoc, asof: datetime) -> C108DTO:
    """
    NfsDoc(domain) -> C108DTO(contracts envelope)

    규칙:
      - labels는 항상 존재(빈 dict라도)
      - c108은 labels를 비우는 것이 정상
      - payload.blocks['리포트'] = list[dict]
    """
    if doc.endpoint_kind != EndpointKind.C108:
        raise ValueError(f"c108_doc_to_dto expects C108 doc, got: {doc.endpoint_kind}")

    # contracts payload 구조에 맞게: blocks/labels를 항상 구성
    blocks: C108Blocks = {"리포트": []}

    # block_keys를 따르되, 실질적으로는 '리포트' 하나만 있어도 충분
    for bk in get_block_keys(EndpointKind.C108):
        if bk != "리포트":
            continue

        block = doc.blocks.get(bk)
        if isinstance(block, RecordsBlock):
            blocks["리포트"] = _to_list_of_dict(block.rows)
        else:
            # 혹시 구조가 섞였으면 최대한 안전하게 빈 값
            blocks["리포트"] = []

    payload: C108Payload = {"blocks": blocks}

    return C108DTO(
        code=doc.code,
        asof=asof,
        endpoint=endpoint,
        payload=payload,
    )


class IngestC108:
    def __init__(self, fetch: FetchC108, sink: NfsSinkPort[C108DTO]):
        self.fetch = fetch
        self.sink = sink

    async def execute(
        self, code: str, *, sleep_sec: float = 2.0, asof: datetime | None = None
    ) -> C108DTO:
        asof = asof or utcnow()

        doc = await self.fetch.execute(code, sleep_sec=sleep_sec)
        logger.debug(f"doc:\n{doc}")
        if doc is None:
            raise RuntimeError(f"c108 fetch returned None: code={code}")

        dto = c108_doc_to_dto(doc=doc, asof=asof)
        logger.debug(f"dto:\n{dto}")

        await self.sink.write(dto, endpoint=endpoint)
        return dto

    async def execute_many(
        self,
        codes: Iterable[str],
        *,
        sleep_sec: float = 2.0,
        asof: Optional[datetime] = None,
    ) -> list[C108DTO]:
        batch_asof = asof or utcnow()

        docs = await self.fetch.execute_many(codes, sleep_sec=sleep_sec)
        dtos = [c108_doc_to_dto(doc=d, asof=batch_asof) for d in docs]
        logger.debug(f"dtos:\n{dtos}")
        await self.sink.write_many(dtos, endpoint=endpoint)
        return dtos
