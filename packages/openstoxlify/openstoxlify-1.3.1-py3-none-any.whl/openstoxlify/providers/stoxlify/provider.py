# pyright: reportAttributeAccessIssue=false
from datetime import timezone, datetime
from typing import List


from .proto import client
from .proto.market import market_pb2, market_pb2_grpc
from .proto.trade import trade_pb2, trade_pb2_grpc
from .proto.model import model_pb2

from ...utils.period import find_range_interval
from ...utils.time import to_google_timestamp
from ...models.enum import ActionType, DefaultProvider, Period
from ...models.series import ActionSeries
from ...models.model import Quote


class Provider:
    def __init__(self, source: DefaultProvider):
        self._source = source

    def source(self) -> str:
        return self._source.value

    def quotes(
        self,
        symbol: str,
        period: Period,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> List[Quote]:
        range_interval = find_range_interval(period)
        try:
            c = client.channel()
            stub = market_pb2_grpc.MarketServiceStub(c)
            req = market_pb2.GetProductInfoRequest(
                Ticker=symbol,
                Range=range_interval.range,
                Interval=range_interval.interval,
                Indicator="quote",
                Source=self._source.value,
            )
            if start is not None:
                req.Start.CopyFrom(to_google_timestamp(start))
            if end is not None:
                req.End.CopyFrom(to_google_timestamp(end))
            response = stub.GetProductInfo(req)
        except Exception as err:
            raise RuntimeError(f"request failed: {err}") from err

        quotes = []
        for q in response.Quote:
            ts = q.Timestamp.ToDatetime().replace(tzinfo=timezone.utc)
            price = q.ProductInfo.Price
            quotes.append(
                Quote(
                    timestamp=ts,
                    high=price.High,
                    low=price.Low,
                    open=price.Open,
                    close=price.Close,
                    volume=price.Volume,
                )
            )
        return quotes

    def authenticate(self, token: str) -> None:
        self._token = token
        return

    def execute(
        self, id: str, symbol: str, action: ActionSeries, amount: float
    ) -> None:
        try:
            a = trade_pb2.Short
            if action.action == ActionType.LONG:
                a = trade_pb2.Long
            task = model_pb2.Task(TaskId=id, Ticker=symbol)
            req = trade_pb2.ExecuteTradeRequest(
                Task=task,
                Action=a,
                Quantity=amount,
            )
            meta = (("authorization", f"Bearer {self._token}"),)
            c = client.channel()
            stub = trade_pb2_grpc.TradeServiceStub(c)
            trade = stub.ExecuteTrade(req, metadata=meta)
        except Exception as err:
            return
