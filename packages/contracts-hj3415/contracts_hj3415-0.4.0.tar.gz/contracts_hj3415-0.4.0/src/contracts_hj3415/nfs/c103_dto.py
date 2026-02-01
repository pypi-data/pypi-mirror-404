# contracts_hj3415/nfs/c103_dto.py
from __future__ import annotations

from typing_extensions import TypedDict
from .nfs_dto import NfsDTO
from .types import Num, MetricKey, PeriodKey


C103ValuesMap = dict[PeriodKey, Num]

class C103Blocks(TypedDict):
    손익계산서y: dict[MetricKey, C103ValuesMap]
    손익계산서q: dict[MetricKey, C103ValuesMap]
    재무상태표y: dict[MetricKey, C103ValuesMap]
    재무상태표q: dict[MetricKey, C103ValuesMap]
    현금흐름표y: dict[MetricKey, C103ValuesMap]
    현금흐름표q: dict[MetricKey, C103ValuesMap]


class C103Labels(TypedDict):
    손익계산서y: dict[MetricKey, str]
    손익계산서q: dict[MetricKey, str]
    재무상태표y: dict[MetricKey, str]
    재무상태표q: dict[MetricKey, str]
    현금흐름표y: dict[MetricKey, str]
    현금흐름표q: dict[MetricKey, str]


class C103Payload(TypedDict):
    blocks: C103Blocks
    labels: C103Labels


class C103DTO(NfsDTO):
    payload: C103Payload
