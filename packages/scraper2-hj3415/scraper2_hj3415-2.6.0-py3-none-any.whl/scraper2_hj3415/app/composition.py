# scraper2_hj3415/app/composition.py
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

from pymongo.asynchronous.database import AsyncDatabase

from scraper2_hj3415.app.ports.browser.browser_factory_port import BrowserFactoryPort
from scraper2_hj3415.app.adapters.out.playwright.browser_factory import (
    PlaywrightBrowserFactory,
)

from scraper2_hj3415.app.services.fetch.fetch_c101 import FetchC101
from scraper2_hj3415.app.services.fetch.fetch_c103 import FetchC103
from scraper2_hj3415.app.services.fetch.fetch_c104 import FetchC104
from scraper2_hj3415.app.services.fetch.fetch_c106 import FetchC106
from scraper2_hj3415.app.services.fetch.fetch_c108 import FetchC108

from scraper2_hj3415.app.usecases.ingest.ingest_c101 import IngestC101
from scraper2_hj3415.app.usecases.ingest.ingest_c103 import IngestC103
from scraper2_hj3415.app.usecases.ingest.ingest_c104 import IngestC104
from scraper2_hj3415.app.usecases.ingest.ingest_c106 import IngestC106
from scraper2_hj3415.app.usecases.ingest.ingest_c108 import IngestC108


from scraper2_hj3415.app.ports.sinks.nfs_sink_port import NfsSinkPort
from contracts_hj3415.nfs.c101_dto import C101DTO
from contracts_hj3415.nfs.c103_dto import C103DTO
from contracts_hj3415.nfs.c104_dto import C104DTO
from contracts_hj3415.nfs.c106_dto import C106DTO
from contracts_hj3415.nfs.c108_dto import C108DTO

from scraper2_hj3415.app.adapters.out.sinks.mongo_sink import MongoSink
from scraper2_hj3415.app.adapters.out.sinks.memory_sink import MemorySink

from scraper2_hj3415.app.adapters.out.sinks.store import InMemoryStore

from db2_hj3415.mongo import Mongo

from scraper2_hj3415.app.domain.types import Sink


def _env_bool(key: str, default: bool) -> bool:
    v = os.getenv(key)
    return (
        default if v is None else v.strip().lower() in {"1", "true", "yes", "y", "on"}
    )


def _env_int(key: str, default: int) -> int:
    v = os.getenv(key)
    if v is None:
        return default
    try:
        return int(v)
    except ValueError:
        return default


def build_browser_factory() -> BrowserFactoryPort:
    return PlaywrightBrowserFactory(
        headless=_env_bool("SCRAPER_HEADLESS", True),
        timeout_ms=_env_int("SCRAPER_TIMEOUT_MS", 20_000),
        max_concurrency=_env_int("SCRAPER_MAX_CONCURRENCY", 2),
    )


# -------------------------
# Bundles
# -------------------------


@dataclass(frozen=True)
class FetchUsecases:
    c101: FetchC101
    c103: FetchC103
    c104: FetchC104
    c106: FetchC106
    c108: FetchC108


@dataclass(frozen=True)
class Sinks:
    c101: NfsSinkPort[C101DTO]
    c103: NfsSinkPort[C103DTO]
    c104: NfsSinkPort[C104DTO]
    c106: NfsSinkPort[C106DTO]
    c108: NfsSinkPort[C108DTO]


@dataclass(frozen=True)
class IngestUsecases:
    c101: IngestC101
    c103: IngestC103
    c104: IngestC104
    c106: IngestC106
    c108: IngestC108


@dataclass(frozen=True)
class Usecases:
    fetch: FetchUsecases
    ingest: IngestUsecases
    sinks: Sinks
    store: InMemoryStore | None = None  # ✅ memory일 때만
    mongo: Mongo | None = None  # ✅ mongo일 때만
    db: AsyncDatabase | None = None  # ✅ mongo일 때만
    browser_factory: Optional[BrowserFactoryPort] = None

    async def aclose(self) -> None:
        if self.browser_factory is not None:
            await self.browser_factory.aclose()

        if self.mongo is not None:
            await self.mongo.close()


# -------------------------
# builders
# -------------------------


def build_fetch_usecases(*, factory: BrowserFactoryPort) -> FetchUsecases:
    return FetchUsecases(
        c101=FetchC101(factory=factory),
        c103=FetchC103(factory=factory),
        c104=FetchC104(factory=factory),
        c106=FetchC106(factory=factory),
        c108=FetchC108(factory=factory),
    )


@dataclass(frozen=True)
class MemoryBundle:
    store: InMemoryStore
    sinks: Sinks


def build_memory_bundle() -> MemoryBundle:
    store = InMemoryStore()
    c101_sink: NfsSinkPort[C101DTO] = MemorySink(store)
    c103_sink: NfsSinkPort[C103DTO] = MemorySink(store)
    c104_sink: NfsSinkPort[C104DTO] = MemorySink(store)
    c106_sink: NfsSinkPort[C106DTO] = MemorySink(store)
    c108_sink: NfsSinkPort[C108DTO] = MemorySink(store)
    sinks = Sinks(
        c101=c101_sink,
        c103=c103_sink,
        c104=c104_sink,
        c106=c106_sink,
        c108=c108_sink,
    )
    return MemoryBundle(store=store, sinks=sinks)


# ---- mongo bundle ----


@dataclass(frozen=True)
class MongoBundle:
    mongo: Mongo
    db: AsyncDatabase
    sinks: Sinks


def build_mongo_bundle() -> MongoBundle:
    mongo = Mongo()  # settings는 db2가 env로 읽음 (DB2_MONGO_URI 등)
    db = mongo.get_db()
    c101_sink: NfsSinkPort[C101DTO] = MongoSink(db)
    c103_sink: NfsSinkPort[C103DTO] = MongoSink(db)
    c104_sink: NfsSinkPort[C104DTO] = MongoSink(db)
    c106_sink: NfsSinkPort[C106DTO] = MongoSink(db)
    c108_sink: NfsSinkPort[C108DTO] = MongoSink(db)
    sinks = Sinks(
        c101=c101_sink,
        c103=c103_sink,
        c104=c104_sink,
        c106=c106_sink,
        c108=c108_sink,
    )
    return MongoBundle(mongo=mongo, db=db, sinks=sinks)


def build_ingest_usecases(*, fetch: FetchUsecases, sinks: Sinks) -> IngestUsecases:
    return IngestUsecases(
        c101=IngestC101(fetch=fetch.c101, sink=sinks.c101),
        c103=IngestC103(fetch=fetch.c103, sink=sinks.c103),
        c104=IngestC104(fetch=fetch.c104, sink=sinks.c104),
        c106=IngestC106(fetch=fetch.c106, sink=sinks.c106),
        c108=IngestC108(fetch=fetch.c108, sink=sinks.c108),
    )


def build_usecases(
    *, factory: BrowserFactoryPort | None = None, sink: Sink = "memory"
) -> Usecases:
    factory = factory or build_browser_factory()
    fetch = build_fetch_usecases(factory=factory)

    if sink == "memory":
        bundle = build_memory_bundle()
        ingest = build_ingest_usecases(fetch=fetch, sinks=bundle.sinks)
        return Usecases(
            fetch=fetch,
            ingest=ingest,
            sinks=bundle.sinks,
            store=bundle.store,
            browser_factory=factory,
        )

    if sink == "mongo":
        bundle = build_mongo_bundle()
        ingest = build_ingest_usecases(fetch=fetch, sinks=bundle.sinks)
        return Usecases(
            fetch=fetch,
            ingest=ingest,
            sinks=bundle.sinks,
            mongo=bundle.mongo,
            db=bundle.db,
            browser_factory=factory,
        )

    raise ValueError(f"Unknown sink_kind: {sink}")
