# scraper2_hj3415/app/domain/blocks.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence
from scraper2_hj3415.app.domain.constants import BLOCK_KEYS_BY_ENDPOINT
from scraper2_hj3415.app.domain.endpoint import EndpointKind
from scraper2_hj3415.app.domain.types import BlockKey, MetricKey, Record
from scraper2_hj3415.app.domain.series import MetricSeries


def _validate_block_key(endpoint_kind: EndpointKind, block_key: str) -> None:
    allowed = BLOCK_KEYS_BY_ENDPOINT.get(endpoint_kind)
    if allowed is not None and block_key not in allowed:
        raise ValueError(f"Invalid block key for {endpoint_kind}: {block_key!r}")


@dataclass(frozen=True)
class MetricsBlock:
    endpoint_kind: EndpointKind
    block_key: BlockKey
    metrics: Mapping[MetricKey, MetricSeries]

    def __post_init__(self) -> None:
        _validate_block_key(self.endpoint_kind, self.block_key)

        # 컨테이너 키와 엔티티 키 불일치 방지(선택)
        for k, m in self.metrics.items():
            if m.key != k:
                raise ValueError(
                    f"Metric key mismatch: map key={k!r} != series key={m.key!r}"
                )

    def get(self, key: MetricKey) -> MetricSeries | None:
        m = self.metrics.get(key)
        if m and m.key != key:
            raise ValueError("Metric key mismatch")
        return m


# 다양한 블록형태 구성 추후 수정필요


@dataclass(frozen=True)
class RecordsBlock:
    endpoint_kind: EndpointKind
    block_key: BlockKey
    rows: Sequence[Record]

    def __post_init__(self) -> None:
        _validate_block_key(self.endpoint_kind, self.block_key)


@dataclass(frozen=True)
class KvBlock:
    endpoint_kind: EndpointKind
    block_key: BlockKey
    values: Mapping[str, Any]


BlockData = MetricsBlock | RecordsBlock | KvBlock
