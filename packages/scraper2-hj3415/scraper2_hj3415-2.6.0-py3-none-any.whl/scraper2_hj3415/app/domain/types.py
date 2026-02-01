# scraper2_hj3415/app/domain/types.py
from __future__ import annotations

from typing import Mapping, Any, Sequence, TypeAlias, Literal

BlockKey = str
MetricKey = str
Period = str
Num = float | int | None

Record: TypeAlias = Mapping[str, Any]
Records: TypeAlias = Sequence[Record]
RawLabel = str
LabelsMap = dict[MetricKey, RawLabel]

Sink = Literal["memory", "mongo"]



