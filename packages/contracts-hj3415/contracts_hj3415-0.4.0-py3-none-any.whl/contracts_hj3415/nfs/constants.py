# contracts_hj3415/nfs/constants.py
from __future__ import annotations


ENDPOINTS: tuple[str, ...] = ("c101", "c103", "c104", "c106", "c108")


C101_BLOCK_KEYS: tuple[str, ...] = (
    "요약",
    "시세",
    "주주현황",
    "기업개요",
    "펀더멘털",
    "어닝서프라이즈",
    "연간컨센서스",
)


C103_BLOCK_KEYS: tuple[str, ...] = (
    "손익계산서y",
    "손익계산서q",
    "재무상태표y",
    "재무상태표q",
    "현금흐름표y",
    "현금흐름표q",
)


C104_BLOCK_KEYS: tuple[str, ...] = (
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
)


C106_BLOCK_KEYS: tuple[str, ...] = (
    "y",
    "q",
)


C108_BLOCK_KEYS: tuple[str, ...] = ("리포트",)
