from datetime import datetime
from typing import List, Dict

from openstoxlify.utils.token import fetch_id, fetch_token

from .models.contract import Provider
from .models.enum import ActionType, PlotType
from .models.series import ActionSeries, FloatSeries
from .models.model import Period, PlotData, Quote


class Context:
    """
    Central context manager for trading strategies.

    The Context class manages market data fetching, indicator plotting,
    and trading signal generation in a unified interface. It provides
    caching for market data and organizes plots by type and screen index.

    Attributes:
        _symbol (str): Trading symbol (e.g., "BTC-USD", "AAPL")
        _period (Period): Timeframe for market data
        _provider (Provider): Data provider instance
        _quotes (List[Quote]): Cached market quotes
        _quotes_mapped (Dict[str, List[Quote]]): Symbol-to-quotes mapping
        _plots (Dict[str, List[PlotData]]): Organized plot data by type
        _signals (List[ActionSeries]): Trading signals timeline
        _token (str): Authentication token for provider
        _authenticated (bool): Authentication status

    Example:
        >>> provider = Provider(DefaultProvider.YFinance)
        >>> ctx = Context(provider, "AAPL", Period.DAILY)
        >>> quotes = ctx.quotes()
        >>> ctx.plot("SMA 20", PlotType.LINE, FloatSeries(ts, value))
        >>> ctx.signal(ActionSeries(ts, ActionType.LONG, 1.0))
    """

    def __init__(
        self, agrv: List[str], provider: Provider, symbol: str, period: Period
    ):
        """
        Initialize a new trading context.

        Args:
            agrv (List[str]): Script's input arguments
            provider (Provider): Data provider instance for fetching market data
            symbol (str): Trading symbol (e.g., "BTC-USD", "AAPL")
            period (Period): Timeframe for candles (DAILY, HOURLY, etc.)

        Example:
            >>> from openstoxlify.providers.stoxlify.provider import Provider
            >>> provider = Provider(DefaultProvider.YFinance)
            >>> ctx = Context(provider, "BTC-USD", Period.DAILY)
        """
        self._symbol = symbol
        self._period = period
        self._provider = provider

        self._quotes: List[Quote] = []
        self._quotes_mapped: Dict[str, List[Quote]] = {}
        self._plots: Dict[str, List[PlotData]] = {}
        self._signals: List[ActionSeries] = []

        self._authenticated: bool = False
        self._token: str | None = fetch_token(agrv)
        self._id: str | None = fetch_id(agrv)

    def quotes(
        self, start: datetime | None = None, end: datetime | None = None
    ) -> List[Quote]:
        """
        Fetch and cache market data quotes.

        Retrieves OHLCV (Open, High, Low, Close, Volume) data from the
        configured provider. Results are cached per symbol to avoid
        redundant API calls.

        Returns:
            List[Quote]: List of market quotes with OHLCV data

        Example:
            >>> quotes = ctx.quotes()
            >>> for quote in quotes:
            ...     print(f"{quote.timestamp}: {quote.close}")

        Note:
            Subsequent calls for the same symbol return cached data.
        """
        quotes = self._quotes_mapped.get(self._symbol)
        if quotes is not None:
            return quotes

        self._quotes = self._provider.quotes(self._symbol, self._period, start, end)
        self._quotes_mapped[self._symbol] = self._quotes
        return self._quotes

    def plot(
        self, label: str, plot_type: PlotType, data: FloatSeries, screen_index: int = 0
    ):
        """
        Add indicator data for visualization.

        Plots are organized by type (LINE, HISTOGRAM, AREA) and screen index.
        Multiple data points with the same label are grouped together.

        Args:
            label (str): Display name for the indicator (e.g., "SMA 20")
            plot_type (PlotType): Visualization type (LINE, HISTOGRAM, AREA)
            data (FloatSeries): Data point with timestamp and value
            screen_index (int, optional): Subplot index. 0 = main chart,
                1+ = separate panels. Defaults to 0.

        Raises:
            ValueError: If plot_type is not a valid PlotType enum

        Example:
            >>> # Plot on main chart
            >>> ctx.plot("Price", PlotType.LINE, FloatSeries(ts, price), 0)
            >>>
            >>> # Plot MACD on separate panel
            >>> ctx.plot("MACD", PlotType.HISTOGRAM, FloatSeries(ts, macd), 1)

        Note:
            Call this method multiple times with the same label to build
            a time series. Data points are automatically grouped by label.
        """
        if plot_type not in PlotType:
            raise ValueError(f"Invalid plot type: {plot_type}")

        key = plot_type.value
        if key not in self._plots:
            self._plots[key] = []

        for plot_entry in self._plots[key]:
            if plot_entry.label == label:
                plot_entry.data.append(data)
                return

        self._plots[key].append(
            PlotData(label=label, data=[data], screen_index=screen_index)
        )

    def signal(self, data: ActionSeries):
        """
        Record a trading signal.

        Signals represent trading decisions (LONG, SHORT, HOLD) at specific
        timestamps. HOLD actions automatically have their amount set to 0.

        Args:
            data (ActionSeries): Trading signal with timestamp, action, and amount

        Example:
            >>> # Buy signal
            >>> ctx.signal(ActionSeries(
            ...     timestamp=quote.timestamp,
            ...     action=ActionType.LONG,
            ...     amount=1.5
            ... ))
            >>>
            >>> # Sell signal
            >>> ctx.signal(ActionSeries(
            ...     timestamp=quote.timestamp,
            ...     action=ActionType.SHORT,
            ...     amount=2.0
            ... ))

        Note:
            Signals are displayed as markers on the price chart with
            annotations showing the action type and amount.
        """
        data.amount = 0.0 if data.action == ActionType.HOLD else data.amount

        self._signals.append(data)

    def authenticate(self):
        """
        Authenticate with the data provider.

        Authentication is required for live trading execution. The token
        is validated with the provider before enabling execution.

        Args:
            token (str): Authentication token/API key from provider

        Example:
            >>> ctx.authenticate("your-api-token-here")
            >>> if ctx._authenticated:
            ...     ctx.execute()  # Can now execute trades
        """
        if not self._token:
            return

        try:
            self._provider.authenticate(self._token)
            self._authenticated = True
        except Exception:
            self._authenticated = False

    def execute(self, offset: int = 0):
        """
        Execute the latest trading signal.

        Executes the signal at the most recent timestamp if:
        1. Context is authenticated
        2. A signal exists at the latest quote timestamp
        3. The signal action is not HOLD

        The execution is delegated to the provider's execute method.

        Args:
            offset (int): trade at latest candle - offset

        Example:
            >>> ctx.authenticate("api-token")
            >>> ctx.signal(ActionSeries(latest_ts, ActionType.LONG, 1.0))
            >>> ctx.execute()  # Places order via provider

        Note:
            This method is intended for live trading. In backtesting mode,
            signals are only recorded for analysis, not executed.
        """
        if not self._authenticated or not self._token:
            return

        self._quotes.sort(key=lambda q: q.timestamp)
        latest = self._quotes[-1 - offset].timestamp
        hashmap = {s.timestamp: s for s in self._signals}

        signal = hashmap.get(latest)
        if signal is None:
            return

        match signal.action:
            case ActionType.HOLD:
                return

        if not self._id:
            self._id = ""

        self._provider.execute(self._id, self._symbol, signal, signal.amount)

    def plots(self) -> Dict[str, List[PlotData]]:
        """
        Get all plot data organized by type.

        Returns:
            Dict[str, List[PlotData]]: Plot data grouped by type
                (e.g., {"line": [...], "histogram": [...]})

        Example:
            >>> plots = ctx.plots()
            >>> for plot_type, plot_list in plots.items():
            ...     print(f"{plot_type}: {len(plot_list)} plots")
        """
        return self._plots

    def signals(self) -> List[ActionSeries]:
        """
        Get all recorded trading signals.

        Returns:
            List[ActionSeries]: Chronological list of trading signals

        Example:
            >>> signals = ctx.signals()
            >>> for signal in signals:
            ...     print(f"{signal.timestamp}: {signal.action} {signal.amount}")
        """
        return self._signals

    def symbol(self) -> str:
        """
        Get the trading symbol.

        Returns:
            str: Trading symbol (e.g., "BTC-USD", "AAPL")
        """
        return self._symbol

    def period(self) -> Period:
        """
        Get the timeframe period.

        Returns:
            Period: Candle period (DAILY, HOURLY, etc.)
        """
        return self._period

    def provider(self) -> Provider:
        """
        Get the data provider instance.

        Returns:
            Provider: Configured data provider
        """
        return self._provider

    def authenticated(self) -> bool:
        """
        Get the authentication status.

        Returns:
            bool: Authentication status of a user
        """
        return self._authenticated

    def id(self) -> str | None:
        """
        Get the context id.

        Returns:
            str | None: current context's unique identifier
        """
        return self._id
