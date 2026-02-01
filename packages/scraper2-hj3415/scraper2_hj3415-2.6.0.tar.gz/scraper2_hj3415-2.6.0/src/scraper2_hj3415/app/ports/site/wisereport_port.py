# scraper2_hj3415/app/ports/site/wisereport_port.py
from __future__ import annotations
from typing import Protocol

class WiseReportPort(Protocol):
    async def ensure_yearly_consensus_open_in_table_nth(
        self,
        *,
        table_selector: str,   # 예: TABLE_XPATH ("xpath=//div[@id='wrapper']//div//table")
        table_index: int,      # 예: TABLE_INDEX (2)
        after_click_sleep_ms: int = 150,
        max_rounds: int = 6,
        wait_timeout_sec: float = 12.0,
    ) -> bool: ...
    async def click_steps(
            self,
            steps: list[tuple[str, str]],
            *,
            jitter_sec: float = 0.6,
    ) -> None: ...