# scraper2_hj3415/cli.py
from __future__ import annotations

import asyncio
from typing import Any, cast, get_args


import time
import typer
from datetime import datetime, timezone

from db2_hj3415.nfs.repo import ensure_indexes
from db2_hj3415.settings import get_settings
from db2_hj3415.universe.repo import list_universe_codes

from scraper2_hj3415.app.composition import build_usecases
from scraper2_hj3415.app.ports.ingest.nfs_ingest_port import NfsIngestPort
from scraper2_hj3415.app.domain.types import Sink

from contracts_hj3415.nfs.types import Endpoints
from contracts_hj3415.universe.types import UniverseNames

from logging_hj3415 import setup_logging, current_log_level, reset_logging, to_pretty_json

setup_logging()
# 운영시에는 아래 항목 주석처리하고 환경변수로 제어할것
reset_logging("DEBUG")
print(f"Current log level - {current_log_level()}")


app = typer.Typer(no_args_is_help=True)

nfs_app = typer.Typer(no_args_is_help=True, help="NFS 수집/저장")
mi_app = typer.Typer(no_args_is_help=True, help="(reserved) MI commands")

app.add_typer(nfs_app, name="nfs")
app.add_typer(mi_app, name="mi")


# -------------------------
# small helpers
# -------------------------

def _endpoint_list(endpoint: str) -> list[str]:
    if endpoint == "all":
        return list(get_args(Endpoints))  # -> ["c101", "c103", "c104", "c106", "c108"]
    return [endpoint]

async def _mongo_bootstrap(db) -> None:
    s = get_settings()
    await ensure_indexes(db, snapshot_ttl_days=s.SNAPSHOT_TTL_DAYS)

async def _run_ingest_with_progress(
    *,
    ucs: Any,
    endpoint: str,
    codes: list[str],
    sleep_sec: float,
    show: bool,
    show_n: int,
    asof: datetime,
    chunk_size: int = 10,
    progress_every: int = 1,
) -> None:
    total = len(codes)
    if total == 0:
        typer.echo("(no codes)")
        return

    t0 = time.perf_counter()   # ✅ 시작 시각
    run_asof = asof

    def _chunks(xs: list[str], n: int):
        for i in range(0, len(xs), n):
            yield xs[i:i + n]

    async def _run_one_endpoint(ep: str) -> None:
        ingest_uc = cast(NfsIngestPort, getattr(ucs.ingest, ep))

        ok = 0
        fail = 0

        typer.echo(f"\n=== START: {ep} === total={total}, chunk_size={chunk_size}")

        for idx, batch in enumerate(_chunks(codes, chunk_size), start=1):
            try:
                results = await ingest_uc.execute_many(batch, sleep_sec=sleep_sec, asof=run_asof)
                ok += sum(1 for r in results if r is not None)
            except Exception as e:
                fail += len(batch)
                typer.echo(f"[WARN] batch failed: {e!r}")

            done = min(idx * chunk_size, total)

            if progress_every > 0 and (idx % progress_every == 0 or done == total):
                typer.echo(f"progress: {done}/{total} (ok={ok}, fail={fail})")

        typer.echo(f"=== DONE: {ep} === ok={ok}, fail={fail}, total={total}")

    # --- 실제 실행 ---
    for ep in _endpoint_list(endpoint):
        await _run_one_endpoint(ep)

    elapsed = time.perf_counter() - t0   # ✅ 종료 시각
    typer.echo(f"\n⏱ elapsed time: {_format_elapsed(elapsed)}")


def _format_elapsed(sec: float) -> str:
    if sec < 60:
        return f"{sec:.1f}s"
    m, s = divmod(int(sec), 60)
    if m < 60:
        return f"{m}m {s}s"
    h, m = divmod(m, 60)
    return f"{h}h {m}m {s}s"

def _parse_asof(asof: str | None) -> datetime:
    """
    Parse ISO8601 string to timezone-aware UTC datetime.
    Accepts:
      - 2026-01-09T05:00:00+00:00
      - 2026-01-09T05:00:00Z
      - 2026-01-09T05:00:00  (treated as UTC)
    """
    if not asof:
        return datetime.now(timezone.utc)

    s = asof.strip()
    if not s:
        return datetime.now(timezone.utc)

    # allow trailing 'Z'
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"

    try:
        dt = datetime.fromisoformat(s)
    except ValueError as e:
        raise typer.BadParameter(
            f"--asof must be ISO8601 datetime (e.g. 2026-01-09T05:00:00Z). got={asof!r}"
        ) from e

    # if naive, assume UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    # normalize to UTC
    return dt.astimezone(timezone.utc)

# -------------------------
# nfs subcommands: one / all
# -------------------------

@nfs_app.command("one")
def nfs_one(
    endpoint: str = typer.Argument(..., help="c101|c103|c104|c106|c108|all"),
    code: str = typer.Argument(..., help="종목코드 (예: 005930)"),
    sleep_sec: float = typer.Option(2.0, "--sleep"),
    sink: Sink = typer.Option("memory", "--sink"),
    show: bool = typer.Option(False, "--show/--no-show", help="결과 DTO 출력"),
    asof: str | None = typer.Option(None, "--asof", help="배치 기준시각(ISO8601, UTC 권장). 예: 2026-01-09T05:00:00Z"),
):
    code = code.strip()
    if not code:
        raise typer.BadParameter("code는 비어있을 수 없습니다.")

    async def _run():
        ucs = build_usecases(sink=sink)

        if sink == "mongo":
            if ucs.db is None:
                raise RuntimeError("mongo sink인데 ucs.db가 없습니다. composition에서 db를 노출하세요.")
            await _mongo_bootstrap(ucs.db)

        try:
            run_asof = _parse_asof(asof)
            for ep in _endpoint_list(endpoint):
                ingest_uc = cast(NfsIngestPort, getattr(ucs.ingest, ep))
                results = await ingest_uc.execute_many([code], sleep_sec=sleep_sec, asof=run_asof)
                dto = results[0] if results else None

                typer.echo(f"\n=== ONE DONE: {ep} {code} ===")
                is_memory_sink = sink == "memory"
                should_show = show or is_memory_sink

                if not should_show:
                    continue

                if dto is None:
                    typer.echo("(no result)")
                else:
                    if is_memory_sink:
                        typer.echo("memory result:")
                    typer.echo(to_pretty_json(dto))
        finally:
            await ucs.aclose()

    asyncio.run(_run())


@nfs_app.command("all")
def nfs_all(
    endpoint: str = typer.Argument(..., help="c101|c103|c104|c106|c108|all"),
    universe: str = typer.Option("krx300", "--universe"),
    limit: int = typer.Option(0, "--limit", help="0=전체"),
    sleep_sec: float = typer.Option(2.0, "--sleep"),
    sink: Sink = typer.Option("mongo", "--sink"),
    chunk_size: int = typer.Option(5, "--chunk", help="진행률 표시용 배치 크기"),
    show: bool = typer.Option(False, "--show/--no-show", help="일부 코드만 출력"),
    show_n: int = typer.Option(3, "--show-n"),
    asof: str | None = typer.Option(None, "--asof", help="배치 기준시각(ISO8601). 예: 2026-01-09T05:00:00Z"),
):
    async def _run():
        ucs = build_usecases(sink=sink)
        if ucs.db is None:
            raise RuntimeError("all 모드는 DB가 필요합니다. mongo sink로 ucs.db를 노출하세요.")
        await _mongo_bootstrap(ucs.db)

        codes = await list_universe_codes(ucs.db, universe=cast(UniverseNames, universe))
        if not codes:
            raise RuntimeError(f"universe='{universe}' codes가 비었습니다. 먼저 krx sync로 universe를 채우세요.")

        if limit and limit > 0:
            codes = codes[:limit]

        run_asof = _parse_asof(asof)

        typer.echo(f"\n=== NFS ALL === universe={universe}, endpoint={endpoint}, codes={len(codes)}, sink={sink}")

        try:
            await _run_ingest_with_progress(
                ucs=ucs,
                endpoint=endpoint,
                codes=codes,
                sleep_sec=sleep_sec,
                show=show,
                show_n=show_n,
                asof=run_asof,
                chunk_size=chunk_size,
                progress_every=1,   # chunk마다
            )
        finally:
            await ucs.aclose()

    asyncio.run(_run())


@mi_app.callback(invoke_without_command=True)
def mi():
    pass


if __name__ == "__main__":
    app()
