# scraper2_hj3415/app/domain/doc.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping
from scraper2_hj3415.app.domain.endpoint import EndpointKind
from scraper2_hj3415.app.domain.types import BlockKey, LabelsMap
from scraper2_hj3415.app.domain.blocks import BlockData


@dataclass(frozen=True)
class NfsDoc:
    code: str
    endpoint_kind: EndpointKind
    blocks: Mapping[BlockKey, BlockData]
    labels: Mapping[BlockKey, LabelsMap]
