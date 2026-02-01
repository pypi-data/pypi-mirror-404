# contracts_hj3415/nfs/c108_dto.py
from __future__ import annotations

from typing_extensions import TypedDict
from .nfs_dto import NfsDTO
from .types import MetricKey


C108ValuesMap = dict[MetricKey, str|int|None]


class C108Blocks(TypedDict):
    리포트: list[C108ValuesMap]


class C108Payload(TypedDict):
    blocks: C108Blocks


class C108DTO(NfsDTO):
    payload: C108Payload
