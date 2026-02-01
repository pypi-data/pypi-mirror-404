from dataclasses import dataclass, asdict
from typing import List, Dict, Any


@dataclass(slots=True)
class PlotOut:
    label: str
    data: List[Dict[str, Any]]
    screen_index: int


@dataclass(slots=True)
class StrategyOut:
    label: str
    data: List[Dict[str, Any]]


@dataclass(slots=True)
class QuoteOut:
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass(slots=True)
class QuotesOut:
    ticker: str
    interval: str
    provider: str
    data: List[QuoteOut]


@dataclass(slots=True)
class Output:
    histogram: List[PlotOut]
    line: List[PlotOut]
    area: List[PlotOut]
    strategy: List[StrategyOut]
    quotes: QuotesOut

    def to_dict(self) -> dict:
        return asdict(self)
