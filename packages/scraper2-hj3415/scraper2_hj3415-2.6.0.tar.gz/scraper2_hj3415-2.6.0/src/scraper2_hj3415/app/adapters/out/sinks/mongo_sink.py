# scraper2_hj3415/app/adapters/out/sinks/mongo_sink.py
from __future__ import annotations

from datetime import datetime
from typing import Iterable

from pymongo.asynchronous.database import AsyncDatabase

from contracts_hj3415.nfs.nfs_dto import NfsDTO
from contracts_hj3415.nfs.types import Endpoints

from db2_hj3415.nfs.repo import (
    upsert_latest_payload,
    upsert_latest_payload_many,
    insert_snapshot_payload,
    insert_snapshots_payload_many,
)


class MongoSink:
    def __init__(self, db: AsyncDatabase):
        self._db = db

    async def write(self, dto: NfsDTO, *, endpoint: Endpoints) -> None:
        code = str(dto.code).strip()
        if not code:
            return

        payload = dict(dto.payload)  # Mapping 방어

        await upsert_latest_payload(
            self._db, endpoint=endpoint, code=code, payload=payload, asof=dto.asof
        )
        await insert_snapshot_payload(
            self._db, endpoint=endpoint, code=code, payload=payload, asof=dto.asof
        )

    async def write_many(
        self,
        dtos: Iterable[NfsDTO],
        *,
        endpoint: Endpoints,
    ) -> None:
        items: dict[str, dict] = {}
        ts: datetime | None = None

        for dto in dtos:
            code = str(dto.code).strip()
            if not code:
                continue
            items[code] = dict(dto.payload)
            if ts is None:
                ts = dto.asof  # 첫 dto의 asof를 배치 기준으로

        if not items:
            return

        await upsert_latest_payload_many(
            self._db, endpoint=endpoint, items=items, asof=ts
        )
        await insert_snapshots_payload_many(
            self._db, endpoint=endpoint, items=items, asof=ts
        )
