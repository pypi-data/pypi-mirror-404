# scraper2_hj3415/app/ports/sinks/nfs_sink_port.py
from __future__ import annotations

from typing import Protocol, Iterable, TypeVar
from contracts_hj3415.nfs.types import Endpoints
from contracts_hj3415.nfs.nfs_dto import NfsDTO

TDto = TypeVar("TDto", bound=NfsDTO)

class NfsSinkPort(Protocol[TDto]):
    async def write(
        self, dto: TDto, *, endpoint: Endpoints
    ) -> None: ...

    async def write_many(
        self,
        dtos: Iterable[TDto],
        *,
        endpoint: Endpoints
    ) -> None: ...
