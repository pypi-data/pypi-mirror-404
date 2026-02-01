# contracts_hj3415/nfs/c101_dto.py
from __future__ import annotations

from typing_extensions import TypedDict
from typing import Any
from .nfs_dto import NfsDTO
from .types import PeriodKey, Num, MetricKey

Scalar = str | float | int | None
ValuesMap = dict[PeriodKey, Num]


class C101Blocks(TypedDict):
    요약: dict[str, Scalar]
    시세: dict[str, Scalar]
    주주현황: list[dict[str, Scalar]]
    기업개요: dict[str, Scalar]
    펀더멘털: dict[MetricKey, ValuesMap]

    어닝서프라이즈: dict[str, Any]
    연간컨센서스: dict[MetricKey, ValuesMap]

class C101Payload(TypedDict):
    blocks: C101Blocks

class C101DTO(NfsDTO):
    payload: C101Payload
