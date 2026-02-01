from datetime import datetime
from typing import List, Protocol, runtime_checkable

from .series import ActionSeries
from .model import Quote
from .enum import Period


@runtime_checkable
class Provider(Protocol):
    def source(self) -> str: ...

    def quotes(
        self,
        symbol: str,
        period: Period,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> List[Quote]: ...

    def authenticate(self, token: str) -> None: ...

    def execute(
        self, id: str, symbol: str, action: ActionSeries, amount: float
    ) -> None: ...
