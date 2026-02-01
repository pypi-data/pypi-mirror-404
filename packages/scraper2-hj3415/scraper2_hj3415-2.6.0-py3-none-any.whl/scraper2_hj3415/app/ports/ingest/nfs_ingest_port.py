# scraper2_hj3415/app/ports/ingest/nfs_ingest_port.py
from __future__ import annotations
from typing import Protocol, Iterable, Optional, TypeVar
from datetime import datetime

from contracts_hj3415.nfs.nfs_dto import NfsDTO

TDto = TypeVar("TDto", bound=NfsDTO)


class NfsIngestPort(Protocol[TDto]):
    async def execute(
        self,
        code: str,
        *,
        sleep_sec: float = ...,
        asof: Optional[datetime] = None,
    ) -> TDto:
        ...

    async def execute_many(
        self,
        codes: Iterable[str],
        *,
        sleep_sec: float = ...,
        asof: Optional[datetime] = None,
    ) -> list[TDto]:
        ...