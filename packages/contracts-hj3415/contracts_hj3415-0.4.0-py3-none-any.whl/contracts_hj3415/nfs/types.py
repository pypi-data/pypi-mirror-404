# contracts_hj3415/nfs/types.py
from __future__ import annotations

from typing import Mapping, Any, Literal, TypeAlias

C101BlockKeys = Literal[
    "요약", "시세", "주주현황", "기업개요", "펀더멘털", "어닝서프라이즈", "연간컨센서스"
]

C103BlockKeys = Literal[
    "손익계산서y",
    "손익계산서q",
    "재무상태표y",
    "재무상태표q",
    "현금흐름표y",
    "현금흐름표q",
]


C104BlockKeys = Literal[
    "수익성y",
    "성장성y",
    "안정성y",
    "활동성y",
    "가치분석y",
    "수익성q",
    "성장성q",
    "안정성q",
    "활동성q",
    "가치분석q",
]


# C106===========================

C106BlockKeys = Literal[
    "y",
    "q",
]


# C108============================

C108BlockKeys = Literal["리포트",]


# General====================

MetricKey = str
PeriodKey = str
CodeKey = str
Num = float | int | None

Endpoints = Literal["c101", "c103", "c104", "c106", "c108"]


Payload = Mapping[str, Any]

BlockKeys: TypeAlias = (
    C101BlockKeys | C103BlockKeys | C104BlockKeys | C106BlockKeys | C108BlockKeys
)
