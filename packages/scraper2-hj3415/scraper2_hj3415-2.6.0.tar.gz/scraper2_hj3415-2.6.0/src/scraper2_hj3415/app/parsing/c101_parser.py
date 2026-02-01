from __future__ import annotations

from typing import Any
from scraper2_hj3415.app.ports.browser.browser_port import BrowserPort
from logging_hj3415 import logger

from .c101.sise import parse_c101_sise_table
from .c101.earning_surprise import parse_c101_earnings_surprise_table
from .c101.fundamentals import parse_c101_fundamentals_table
from .c101.major_shareholders import parse_c101_major_shareholders
from .c101.company_overview import parse_c101_company_overview
from .c101.summary_cmp import parse_c101_summary_cmp_table
from .c101.yearly_consensus import parse_c101_yearly_consensus_table

async def parse_c101_to_dict(browser: BrowserPort) -> dict[str, list[dict[str, Any]]]:
    parsed_summary_cmp = await parse_c101_summary_cmp_table(browser)
    logger.debug(f"parsed_summary_cmp data: {parsed_summary_cmp}")

    parsed_sise = await parse_c101_sise_table(browser)
    logger.debug(f"parsed_sise data: {parsed_sise}")

    parsed_company_overview = await parse_c101_company_overview(browser)
    logger.debug(f"parsed_company_overview data: {parsed_company_overview}")

    parsed_major_shareholders = await parse_c101_major_shareholders(browser)
    logger.debug(f"parsed_major_shareholders data: {parsed_major_shareholders}")

    parsed_fundamentals = await parse_c101_fundamentals_table(browser)
    logger.debug(f"parsed_fundamentals data: {parsed_fundamentals}")

    parsed_earnings_surprise = await parse_c101_earnings_surprise_table(browser)
    logger.debug(f"parsed_earnings_surprise data: {parsed_earnings_surprise}")

    parsed_yearly_consensus = await parse_c101_yearly_consensus_table(browser)
    logger.debug(f"parsed_yearly_consensus data: {parsed_yearly_consensus}")

    return {
        "요약": parsed_summary_cmp,
        "시세": parsed_sise,
        "주주현황": parsed_major_shareholders,
        "기업개요": parsed_company_overview,
        "펀더멘털": parsed_fundamentals,
        "어닝서프라이즈": parsed_earnings_surprise,
        "연간컨센서스": parsed_yearly_consensus,
    }
