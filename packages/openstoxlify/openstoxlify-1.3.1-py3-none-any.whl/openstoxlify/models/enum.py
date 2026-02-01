from enum import Enum


class PlotType(Enum):
    HISTOGRAM = "histogram"
    LINE = "line"
    AREA = "area"
    CANDLESTICK = "candlestick"


class ActionType(Enum):
    LONG = "Long"
    HOLD = "Hold"
    SHORT = "Short"


class Period(Enum):
    MINUTELY = "1m"
    QUINTLY = "5m"
    HALFHOURLY = "30m"
    HOURLY = "60m"
    DAILY = "D"
    WEEKLY = "W"
    MONTHLY = "M"


class DefaultProvider(Enum):
    YFinance = "YFinance"
    Binance = "Binance"
