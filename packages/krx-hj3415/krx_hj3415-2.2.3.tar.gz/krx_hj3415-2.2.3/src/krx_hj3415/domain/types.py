# krx_hj3415/domain/types.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class CodeItem:
    code: str
    name: str
    asof: datetime
    market: str | None = None  # 확장 대비(예: KRX/KOSPI/KOSDAQ/NYSE/NASDAQ 등)


@dataclass(frozen=True)
class UniverseDiff:
    universe: str
    asof: datetime
    added: list[CodeItem]
    removed: list[CodeItem]
    kept_count: int

    @property
    def added_codes(self) -> list[str]:
        return [x.code for x in self.added]

    @property
    def removed_codes(self) -> list[str]:
        return [x.code for x in self.removed]
