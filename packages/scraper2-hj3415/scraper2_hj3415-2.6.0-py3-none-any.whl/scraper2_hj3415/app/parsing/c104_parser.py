# scraper2_hj3415/app/parsing/c104_parser.py
from __future__ import annotations

from typing import Any

from scraper2_hj3415.app.ports.browser.browser_port import BrowserPort
from scraper2_hj3415.app.parsing._tables.html_table import try_html_table_to_df, df_to_c1034_metric_list

TABLE_XPATH = 'xpath=//table[@class="gHead01 all-width data-list"]'


async def parse_c104_current_table(
    browser: BrowserPort,
    *,
    table_index: int,
) -> list[dict[str, Any]]:
    """
    ✅ 현재 화면 상태(탭/연간/분기/검색 결과)가 이미 준비되었다는 전제.
    이 상태에서 지정된 table_index 테이블만 읽어서 rows로 변환한다.
    """
    html = await browser.outer_html_nth(TABLE_XPATH, table_index)
    df = try_html_table_to_df(html)
    return df_to_c1034_metric_list(df)
