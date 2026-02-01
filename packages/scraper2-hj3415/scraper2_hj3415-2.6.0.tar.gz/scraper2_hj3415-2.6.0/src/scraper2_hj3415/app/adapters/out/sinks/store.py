# scraper2_hj3415/app/adapters/out/sinks/store.py
from __future__ import annotations

import asyncio
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Deque, Dict, Generic, Iterable, List, Optional, Tuple, TypeVar

T = TypeVar("T")  # DTO 타입


@dataclass(frozen=True)
class StoreStats:
    endpoint: str
    latest_count: int
    history_count: int


class InMemoryStore(Generic[T]):
    """
    endpoint별로 DTO를 저장한다.
    - latest: endpoint -> key(보통 코드) -> dto
    - history: endpoint -> deque[dto] (최근 max_history개)
    """

    def __init__(self, *, max_history: int = 2000):
        self._lock = asyncio.Lock()
        self._max_history = max_history
        self._history: Dict[str, Deque[T]] = defaultdict(
            lambda: deque(maxlen=max_history)
        )
        self._latest: Dict[str, Dict[str, T]] = defaultdict(dict)

    # ---------- write ----------

    async def put(self, endpoint: str, key: str, dto: T) -> None:
        async with self._lock:
            self._history[endpoint].append(dto)
            self._latest[endpoint][key] = dto

    async def put_many(self, endpoint: str, items: Iterable[Tuple[str, T]]) -> None:
        async with self._lock:
            for key, dto in items:
                self._history[endpoint].append(dto)
                self._latest[endpoint][key] = dto

    # ---------- read ----------

    async def get(self, endpoint: str, key: str) -> Optional[T]:
        async with self._lock:
            return self._latest.get(endpoint, {}).get(key)

    async def all_latest(self, endpoint: str) -> Dict[str, T]:
        async with self._lock:
            return dict(self._latest.get(endpoint, {}))

    async def list_keys(self, endpoint: str) -> List[str]:
        async with self._lock:
            # 정렬은 취향인데, CLI 출력은 정렬이 편해서 기본 정렬
            return sorted(self._latest.get(endpoint, {}).keys())

    async def history(self, endpoint: str) -> List[T]:
        async with self._lock:
            return list(self._history.get(endpoint, []))

    async def stats(self, endpoint: str) -> StoreStats:
        async with self._lock:
            latest_count = len(self._latest.get(endpoint, {}))
            history_count = len(self._history.get(endpoint, []))
            return StoreStats(
                endpoint=endpoint,
                latest_count=latest_count,
                history_count=history_count,
            )

    async def clear(self, endpoint: str | None = None) -> None:
        async with self._lock:
            if endpoint is None:
                self._history.clear()
                self._latest.clear()
            else:
                self._history.pop(endpoint, None)
                self._latest.pop(endpoint, None)
