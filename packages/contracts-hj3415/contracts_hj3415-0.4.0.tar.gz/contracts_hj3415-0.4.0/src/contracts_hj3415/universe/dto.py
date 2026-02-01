# contracts_hj3415/universe/dto.py
from __future__ import annotations

from typing import Any, TypedDict

class UniverseItemDTO(TypedDict, total=False):
    code: str              # required by convention
    name: str
    market: str
    meta: dict[str, Any]


class UniversePayloadDTO(TypedDict):
    universe: str
    asof: str              # ISO string 권장 (UTC). datetime을 넘겨도 되지만 계약은 str이 깔끔함
    source: str
    items: list[UniverseItemDTO]