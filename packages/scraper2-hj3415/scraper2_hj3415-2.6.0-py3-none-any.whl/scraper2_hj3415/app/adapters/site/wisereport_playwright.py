# scraper2_hj3415/app/adapters/site/wisereport_playwright.py
from __future__ import annotations

from scraper2_hj3415.app.ports.browser.browser_port import BrowserPort
from logging_hj3415 import logger


class WiseReportPlaywright:
    def __init__(self, browser: BrowserPort):
        self.browser = browser

    async def ensure_yearly_consensus_open_in_table_nth(
        self,
        *,
        table_selector: str,  # 예: TABLE_XPATH ("xpath=//div[@id='wrapper']//div//table")
        table_index: int,  # 예: TABLE_INDEX (2)
        after_click_sleep_ms: int = 150,
        max_rounds: int = 6,
        wait_timeout_sec: float = 12.0,
    ) -> bool:
        """
        목표: 연간 컨센서스 컬럼이 '반드시 펼쳐진 상태'가 되게 한다.
        전략:
          - TABLE_NTH 스코프 안에서
          - btn_moreY 또는 btn_moreQQ 이면서
          - '연간컨센서스보기' 텍스트를 가진 a 토글들 중
          - computedStyle(display) != 'none' 인 것들을 전부 클릭
          - 클릭마다 테이블 텍스트 변경을 기다림
        """

        table_scoped = f"{table_selector} >> nth={table_index}"

        # table 내부의 토글(a)만 잡기 (btn_moreY / btn_moreQQ 둘 다)
        VIEW_ALL = (
            f"{table_scoped} >> xpath=.//a["
            "("
            "contains(@class,'btn_moreY') or contains(@class,'btn_moreQQ')"
            ")"
            " and .//span[contains(normalize-space(.),'연간컨센서스보기')]"
            "]"
        )

        CLOSE_ALL = (
            f"{table_scoped} >> xpath=.//a["
            "("
            "contains(@class,'btn_moreY') or contains(@class,'btn_moreQQ')"
            ")"
            " and .//span[contains(normalize-space(.),'연간컨센서스닫기')]"
            "]"
        )

        # 테이블 텍스트 변화 감지용 “prev_text”
        prev_text = await self.browser.wait_table_text_changed(
            table_selector,
            index=table_index,
            prev_text=None,
            timeout_sec=wait_timeout_sec,
            min_lines=10,
        )

        logger.debug("ensure_yearly_consensus_open_in_table_nth: start")

        # round를 두는 이유:
        # - 보기 토글이 여러 개고, 클릭할 때 DOM이 재배치될 수 있음
        # - 1번에 다 못 누르면 다음 라운드에서 다시 스캔
        for round_no in range(1, max_rounds + 1):
            view_cnt = await self.browser.count(VIEW_ALL)
            close_cnt = await self.browser.count(CLOSE_ALL)
            logger.debug(
                f"round={round_no} toggle exists: view={view_cnt}, close={close_cnt}"
            )

            # "보기" 토글이 아예 없으면 -> 이미 다 펼쳐져 있거나(닫기만 존재),
            # 혹은 페이지 구조가 달라서 못 찾는 것. 여기서는 '성공'으로 간주.
            if view_cnt == 0:
                logger.debug("no VIEW toggles found in-table -> treat as OPEN")
                return True

            clicked_any = False

            # i를 0..view_cnt-1로 돌면서 display != none 인 것만 클릭
            # (중간에 DOM 바뀌면 count/순서가 바뀔 수 있으니, 실패해도 계속)
            for i in range(view_cnt):
                try:
                    # 혹시 DOM이 바뀌어 index가 사라졌으면 skip
                    if not await self.browser.is_attached(VIEW_ALL, index=i):
                        continue

                    disp = await self.browser.computed_style(
                        VIEW_ALL, index=i, prop="display"
                    )
                    if disp.strip().lower() == "none":
                        continue

                    # 화면 밖이면 클릭 실패할 수 있으니 스크롤
                    await self.browser.scroll_into_view(VIEW_ALL, index=i)

                    # trial(실패해도 진행)
                    _ = await self.browser.try_click(
                        VIEW_ALL, index=i, timeout_ms=1500, force=False
                    )

                    # 실제 클릭
                    try:
                        await self.browser.click(
                            VIEW_ALL, index=i, timeout_ms=4000, force=False
                        )
                    except Exception:
                        await self.browser.click(
                            VIEW_ALL, index=i, timeout_ms=4000, force=True
                        )

                    await self.browser.sleep_ms(after_click_sleep_ms)

                    # 클릭 후 테이블 텍스트 변경 대기
                    prev_text = await self.browser.wait_table_text_changed(
                        table_selector,
                        index=table_index,
                        prev_text=prev_text,
                        timeout_sec=wait_timeout_sec,
                        min_lines=10,
                    )

                    clicked_any = True
                    logger.debug(f"clicked VIEW toggle: idx={i}, display={disp}")

                except Exception as e:
                    logger.debug(
                        f"click VIEW toggle failed: idx={i}, err={type(e).__name__}: {e}"
                    )
                    continue

            # 이번 라운드에서 클릭을 하나도 못 했으면:
            # - 모든 VIEW가 display:none 이었거나
            # - 클릭이 막혔거나
            # => VIEW(display!=none)가 남아있는지 다시 검사
            if not clicked_any:
                remain = await self.browser.count(VIEW_ALL)
                logger.debug(f"no clicks in round; remain VIEW count={remain}")
                # VIEW는 있는데 전부 display:none 이면 사실상 '열림' 상태로 볼 수 있음
                # (닫기만 보이는 케이스)
                # 여기서는 “성공” 처리
                return True

            # 다음 라운드에서 다시 스캔해서 VIEW(display!=none)가 남아있으면 또 클릭
            # (다 눌렀으면 결국 클릭할 게 없어짐)

        # 라운드 다 돌았는데도 여기까지 왔다면,
        # “보기 토글이 계속 display!=none으로 남는다” = 열리지 않는 구조/권한/오버레이 등
        logger.warning("ensure_yearly_consensus_open_in_table_nth: exceeded max_rounds")
        return False

    async def click_steps(
        self,
        steps: list[tuple[str, str]],
        *,
        jitter_sec: float = 0.6,
    ) -> None:
        """
        현재 페이지에서 탭/라디오/검색 버튼 클릭만 수행.
        """
        for _name, selector in steps:
            await self.browser.wait_attached(selector)
            logger.info(f"click step: {_name}")
            await self.browser.click(selector)
            # 서버/클라이언트 부담 줄이기: 작은 지터
            wait = int((0.5 + (jitter_sec * 0.5))*1000)
            await self.browser.sleep_ms(wait)
