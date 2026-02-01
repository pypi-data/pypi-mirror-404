# scraper2_hj3415/app/domain/constants.py
from __future__ import annotations

from typing import Mapping

from contracts_hj3415.nfs.types import BlockKeys
from contracts_hj3415.nfs.constants import C101_BLOCK_KEYS, C103_BLOCK_KEYS, C104_BLOCK_KEYS, C106_BLOCK_KEYS, C108_BLOCK_KEYS
from scraper2_hj3415.app.domain.endpoint import EndpointKind


BLOCK_KEYS_BY_ENDPOINT: Mapping[EndpointKind, tuple[str, ...]] = {
    EndpointKind.C101: C101_BLOCK_KEYS,
    EndpointKind.C103: C103_BLOCK_KEYS,
    EndpointKind.C104: C104_BLOCK_KEYS,
    EndpointKind.C106: C106_BLOCK_KEYS,
    EndpointKind.C108: C108_BLOCK_KEYS,
}


def get_block_keys(endpoint: EndpointKind) -> tuple[str, ...]:
    """
    엔드포인트의 "공식" 블록 키 목록.
    - 도메인 레이어에 두되, selector/table index 같은 구현 디테일은 넣지 않는다.
    """
    return BLOCK_KEYS_BY_ENDPOINT.get(endpoint, ())


def is_known_block(endpoint: EndpointKind, key: BlockKeys) -> bool:
    """
    블록 키가 해당 endpoint의 공식 목록에 포함되는지 여부.
    (검증/필터링/동적 payload merge 등에 사용)
    """
    return key in BLOCK_KEYS_BY_ENDPOINT.get(endpoint, ())