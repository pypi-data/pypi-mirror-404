# scraper2_hj3415/app/services/nfs_doc_builders.py
from __future__ import annotations

from collections import defaultdict
from typing import Mapping, Iterable, Any

from scraper2_hj3415.app.domain.endpoint import EndpointKind
from scraper2_hj3415.app.domain.constants import BLOCK_KEYS_BY_ENDPOINT
from scraper2_hj3415.app.domain.doc import NfsDoc
from scraper2_hj3415.app.domain.blocks import MetricsBlock, RecordsBlock, KvBlock, BlockData
from scraper2_hj3415.app.domain.series import MetricSeries
from scraper2_hj3415.app.domain.types import LabelsMap, MetricKey, Period, Num, BlockKey, Records, Record

from common_hj3415.utils import nan_to_none


def is_all_none(row: dict[str, Any]) -> bool:
    return all(v is None for v in row.values())


ParsedBlocks = Mapping[
    str, Any
]  # parser가 반환한 "block_key(str) -> rows(list[dict])"


def build_metrics_block_and_labels_from_rows(
    *,
    endpoint_kind: EndpointKind,
    block_key: BlockKey,
    rows: Records,
    item_key: str = "항목",
    raw_label_key: str = "항목_raw",
) -> tuple[MetricsBlock, LabelsMap]:
    """
    rows(list[dict]) -> (MetricsBlock, LabelsMap)
    c103/c104/c106 공통 빌더.

    - Metric key는 item_key(보통 '항목')에서 만들고,
      기간 컬럼들은 {Period: Num}으로 유지한다.
    - LabelsMap은 dto_key -> raw_label(정제된 원라벨)
    """
    grouped: dict[str, list[tuple[dict[Period, Num], str]]] = defaultdict(list)

    for r in rows:
        item = r.get(item_key)
        if not item:
            continue

        raw_label = r.get(raw_label_key)
        if raw_label is None:
            raw_label = item

        per_map: dict[Period, Num] = {
            str(k): nan_to_none(v)
            for k, v in r.items()
            if k not in (item_key, raw_label_key)
        }

        grouped[item].append((per_map, raw_label))

    series_map: dict[MetricKey, MetricSeries] = {}
    labels_map: LabelsMap = {}

    for item, pairs in grouped.items():
        if len(pairs) == 1:
            per_map, raw_label = pairs[0]
            series_map[item] = MetricSeries(key=item, values=per_map)
            labels_map[item] = raw_label
            continue

        kept = [(per_map, raw) for (per_map, raw) in pairs if not is_all_none(per_map)]
        if not kept:
            continue

        for idx, (per_map, raw_label) in enumerate(kept, start=1):
            mk = item if idx == 1 else f"{item}_{idx}"
            series_map[mk] = MetricSeries(key=mk, values=per_map)
            labels_map[mk] = raw_label

    block = MetricsBlock(
        endpoint_kind=endpoint_kind, block_key=block_key, metrics=series_map
    )
    return block, labels_map


def build_metrics_doc_from_parsed(
    *,
    code: str,
    endpoint_kind: EndpointKind,
    parsed: ParsedBlocks,
    block_keys: Iterable[BlockKey] | None = None,
    item_key: str = "항목",
    raw_label_key: str = "항목_raw",
    keep_empty_blocks: bool = True,
) -> NfsDoc:
    """
    parser가 만든 dict(블록키 -> rows)를 받아서 NfsDoc(=MetricsBlock들)로 조립.
    - c103/c104/c106 공용으로 사용 가능.

    keep_empty_blocks:
      - True: block은 항상 생성 (metrics 비어도 block 존재)
      - False: rows가 없거나 metrics가 비면 blocks에서 제외
    """
    if block_keys is None:
        block_keys = BLOCK_KEYS_BY_ENDPOINT[endpoint_kind]

    blocks: dict[BlockKey, MetricsBlock] = {}
    labels: dict[BlockKey, LabelsMap] = {}

    for bk in block_keys:
        rows = parsed.get(str(bk), []) or []
        block, lm = build_metrics_block_and_labels_from_rows(
            endpoint_kind=endpoint_kind,
            block_key=bk,
            rows=rows,
            item_key=item_key,
            raw_label_key=raw_label_key,
        )

        if not keep_empty_blocks and not block.metrics:
            continue

        blocks[bk] = block
        labels[bk] = lm  # 비어있어도 {}로 유지

    return NfsDoc(code=code, endpoint_kind=endpoint_kind, blocks=blocks, labels=labels)


def _as_records(x: Any) -> Records:
    """
    안전하게 rows를 Records(=Sequence[Record])로 캐스팅/정리.
    - None/비정상 값이면 빈 리스트
    - list[dict] 형태만 통과시키고 나머지는 필터
    """
    if not x:
        return []
    if not isinstance(x, list):
        return []

    out: list[Record] = []
    for it in x:
        if isinstance(it, dict):
            out.append(it)
    return out


def build_records_block_from_rows(
    *,
    endpoint_kind: EndpointKind,
    block_key: BlockKey,
    rows: Records,
) -> RecordsBlock:
    """
    rows(list[dict]) -> RecordsBlock
    - c108 같은 레코드성 블록(리포트 목록 등)에 사용
    """
    # RecordsBlock 쪽에서도 __post_init__로 block_key 검증이 수행된다는 전제(네가 정돈한 도메인)
    return RecordsBlock(endpoint_kind=endpoint_kind, block_key=block_key, rows=list(rows))


def build_c108_doc_from_parsed(
    *,
    code: str,
    parsed: ParsedBlocks,
    block_keys: Iterable[BlockKey] | None = None,
    keep_empty_blocks: bool = True,
) -> NfsDoc:
    """
    c108 parser 결과(dict)를 받아서 NfsDoc(=RecordsBlock들)로 조립.

    규칙(너가 정한 원칙):
      - labels는 항상 존재(빈 dict라도)
      - c108은 labels를 비우는 것을 정상으로 간주

    keep_empty_blocks:
      - True: block은 항상 생성(rows 비어도 block 존재)
      - False: rows가 비면 blocks에서 제외
    """
    endpoint_kind = EndpointKind.C108

    if block_keys is None:
        # 보통 ("리포트",) 같은 튜플
        block_keys = BLOCK_KEYS_BY_ENDPOINT[endpoint_kind]

    blocks: dict[BlockKey, RecordsBlock] = {}
    labels: dict[BlockKey, LabelsMap] = {}

    for bk in block_keys:
        rows = _as_records(parsed.get(str(bk)))
        block = build_records_block_from_rows(
            endpoint_kind=endpoint_kind,
            block_key=bk,
            rows=rows,
        )

        if not keep_empty_blocks and not block.rows:
            continue

        blocks[bk] = block
        labels[bk] = {}  # c108은 labels 비우는 것이 정상

    return NfsDoc(
        code=code,
        endpoint_kind=endpoint_kind,
        blocks=blocks,
        labels=labels,
    )

def build_kv_block_from_mapping(
    *,
    endpoint_kind: EndpointKind,
    block_key: BlockKey,
    data: Mapping[str, Any] | None,
    keep_empty: bool = True,
) -> KvBlock | None:
    """
    dict 형태 블록을 KvBlock으로 감싼다.
    - c101 요약/시세/기업개요/펀더멘털/어닝서프라이즈 같은 "구조 dict"에 사용
    """
    if not data:
        if not keep_empty:
            return None
        data = {}

    return KvBlock(endpoint_kind=endpoint_kind, block_key=block_key, values=data)


ParsedC101 = Mapping[str, Any]  # c101은 dict/list/dict(중첩) 섞여서 Any가 현실적


def build_c101_doc_from_parsed(
    *,
    code: str,
    parsed: ParsedC101,
    block_keys: Iterable[BlockKey] | None = None,
    keep_empty_blocks: bool = True,
) -> NfsDoc:
    """
    c101 parser 결과(블록별 다양한 타입)를 NfsDoc으로 조립.
    labels는 c101은 '비어도 정상' 규칙을 따르므로 항상 {}로 둔다.
    """
    endpoint_kind = EndpointKind.C101

    if block_keys is None:
        block_keys = BLOCK_KEYS_BY_ENDPOINT[endpoint_kind]

    blocks: dict[BlockKey, BlockData] = {}
    labels: dict[BlockKey, LabelsMap] = {}

    for bk in block_keys:
        v = parsed.get(str(bk))

        # c101 규칙: labels는 비어도 정상, 있으면 넣는 게 아니라 "기본 비움" 추천
        labels[bk] = {}

        # list -> RecordsBlock
        if isinstance(v, list):
            # v: list[dict[str, Any]] 가정 (파서가 그렇게 만들고 있음)
            rb = build_records_block_from_rows(
                endpoint_kind=endpoint_kind,
                block_key=bk,
                rows=v,               # type: ignore[arg-type]  (rows 타입 맞추면 제거 가능)
            )
            if rb is not None:
                blocks[bk] = rb
            continue

        # dict(중첩 포함) -> KvBlock
        if isinstance(v, dict):
            kb = build_kv_block_from_mapping(
                endpoint_kind=endpoint_kind,
                block_key=bk,
                data=v,
                keep_empty=keep_empty_blocks,
            )
            if kb is not None:
                blocks[bk] = kb
            continue

        # None/기타 -> empty policy
        if keep_empty_blocks:
            kb = build_kv_block_from_mapping(
                endpoint_kind=endpoint_kind,
                block_key=bk,
                data={},
                keep_empty=True,
            )
            blocks[bk] = kb

    return NfsDoc(code=code, endpoint_kind=endpoint_kind, blocks=blocks, labels=labels)
