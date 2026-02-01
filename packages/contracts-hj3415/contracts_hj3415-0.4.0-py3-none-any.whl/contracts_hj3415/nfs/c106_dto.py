# contracts_hj3415/nfs/c106_dto.py
from __future__ import annotations

from typing_extensions import TypedDict
from .nfs_dto import NfsDTO
from .types import Num, MetricKey, CodeKey


C106ValuesMap = dict[CodeKey, Num]


class C106Blocks(TypedDict):
    y: dict[MetricKey, C106ValuesMap]
    q: dict[MetricKey, C106ValuesMap]


class C106Labels(TypedDict):
    y: dict[MetricKey, str]
    q: dict[MetricKey, str]


class C106Payload(TypedDict):
    blocks: C106Blocks
    labels: C106Labels


class C106DTO(NfsDTO):
    payload: C106Payload
