from typing import Dict
from ..models.model import Period, RangeInterval


def find_range_interval(period: Period) -> RangeInterval:
    dictionary: Dict[Period, RangeInterval] = {
        Period.MINUTELY: RangeInterval("1m", "1wk"),
        Period.QUINTLY: RangeInterval("5m", "1wk"),
        Period.HALFHOURLY: RangeInterval("30m", "1wk"),
        Period.HOURLY: RangeInterval("60m", "1wk"),
        Period.DAILY: RangeInterval("1d", "1y"),
        Period.WEEKLY: RangeInterval("1wk", "10y"),
        Period.MONTHLY: RangeInterval("1mo", "max"),
    }

    range_interval = dictionary.get(period)
    if range_interval is None:
        raise Exception(f"invalid period mapping {period}")

    return range_interval
