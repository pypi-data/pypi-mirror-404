# scraper2_hj3415/app/adapters/out/sinks/memory_sink.py
from __future__ import annotations

from typing import Iterable

from contracts_hj3415.nfs.nfs_dto import NfsDTO
from contracts_hj3415.nfs.types import Endpoints

from scraper2_hj3415.app.adapters.out.sinks.store import InMemoryStore


class MemorySink:
    def __init__(self, store: InMemoryStore[NfsDTO]):
        self._store = store

    async def write(self, dto: NfsDTO, *, endpoint: Endpoints) -> None:
        await self._store.put(endpoint, dto.code, dto)

    async def write_many(
        self,
        dtos: Iterable[NfsDTO],
        *,
        endpoint: Endpoints,
    ) -> None:
        await self._store.put_many(endpoint, ((d.code, d) for d in dtos))
