from dataclasses import dataclass
from datetime import datetime
from typing import List

from .series import FloatSeries
from .enum import DefaultProvider, Period


@dataclass
class Quote:
    timestamp: datetime
    high: float
    low: float
    open: float
    close: float
    volume: float


@dataclass
class MarketData:
    ticker: str
    period: Period
    provider: DefaultProvider
    quotes: list[Quote]


@dataclass
class PlotData:
    label: str
    data: List[FloatSeries]
    screen_index: int


@dataclass
class RangeInterval:
    interval: str
    range: str
