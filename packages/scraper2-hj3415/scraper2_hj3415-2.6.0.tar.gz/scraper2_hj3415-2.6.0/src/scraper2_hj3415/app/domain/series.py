# scraper2_hj3415/app/domain/series.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping
from scraper2_hj3415.app.domain.types import MetricKey, Period, Num

@dataclass(frozen=True)
class MetricSeries:
    key: MetricKey
    values: Mapping[Period, Num]