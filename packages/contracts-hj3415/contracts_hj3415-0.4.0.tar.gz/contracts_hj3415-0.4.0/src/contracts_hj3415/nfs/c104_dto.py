# contracts_hj3415/nfs/c104_dto.py
from __future__ import annotations

from typing_extensions import TypedDict
from .nfs_dto import NfsDTO
from .types import Num, MetricKey, PeriodKey


C104ValuesMap = dict[PeriodKey, Num]

class C104Blocks(TypedDict):
    수익성y: dict[MetricKey, C104ValuesMap]
    성장성y: dict[MetricKey, C104ValuesMap]
    안정성y: dict[MetricKey, C104ValuesMap]
    활동성y: dict[MetricKey, C104ValuesMap]
    가치분석y: dict[MetricKey, C104ValuesMap]
    수익성q: dict[MetricKey, C104ValuesMap]
    성장성q: dict[MetricKey, C104ValuesMap]
    안정성q: dict[MetricKey, C104ValuesMap]
    활동성q: dict[MetricKey, C104ValuesMap]
    가치분석q: dict[MetricKey, C104ValuesMap]


class C104Labels(TypedDict):
    수익성y: dict[MetricKey, str]
    성장성y: dict[MetricKey, str]
    안정성y: dict[MetricKey, str]
    활동성y: dict[MetricKey, str]
    가치분석y: dict[MetricKey, str]
    수익성q: dict[MetricKey, str]
    성장성q: dict[MetricKey, str]
    안정성q: dict[MetricKey, str]
    활동성q: dict[MetricKey, str]
    가치분석q: dict[MetricKey, str]



class C104Payload(TypedDict):
    blocks: C104Blocks
    labels: C104Labels


class C104DTO(NfsDTO):
    payload: C104Payload
