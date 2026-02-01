import random
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from typing import Any, Dict, List, Tuple
from datetime import datetime

from .context import Context
from .utils.color import color_palette
from .utils.output import output
from .models.enum import PlotType, ActionType


class Canvas:
    """
    Professional financial chart renderer.

    The Canvas class generates multi-panel matplotlib charts combining:
    - OHLC candlestick charts
    - Technical indicators (lines, histograms, areas)
    - Trading signal markers and annotations
    - Multiple subplot panels with independent scales

    Attributes:
        _plot_data (Dict): Indicator data organized by plot type
        _market_data (List[Quote]): OHLCV market quotes
        _strategy_data (List[ActionSeries]): Trading signals
        _color_map (Dict[str, str]): Label-to-color mapping for consistency

    Example:
        >>> canvas = Canvas(ctx)
        >>> canvas.draw(
        ...     figsize=(16, 9),
        ...     title="My Trading Strategy",
        ...     show_legend=True
        ... )
    """

    def __init__(self, ctx: Context):
        """
        Initialize canvas from trading context.

        Args:
            ctx (Context): Trading context containing market data, plots,
                and signals

        Example:
            >>> provider = Provider(DefaultProvider.YFinance)
            >>> ctx = Context(provider, "AAPL", Period.DAILY)
            >>> canvas = Canvas(ctx)
        """
        self._ctx = ctx
        self._plot_data = ctx.plots()
        self._market_data = ctx.quotes()
        self._strategy_data = ctx.signals()

        self._color_map: Dict[str, str] = {}

    def _get_color(self, label: str) -> str:
        """
        Get or assign a consistent color for a label.

        Colors are randomly assigned from the palette and cached to ensure
        the same label always gets the same color across the chart.

        Args:
            label (str): Indicator label (e.g., "SMA 20")

        Returns:
            str: Hex color code (e.g., "#FF5733")

        Note:
            Uses color_palette() from utils.common for predefined colors.
        """
        opts = color_palette()
        if label not in self._color_map:
            self._color_map[label] = random.choice(opts)
        return self._color_map[label]

    def _has_plotting_data(self) -> bool:
        """
        Check if there's any data to plot.

        Returns:
            bool: True if market data, signals, or plot data exists

        Note:
            Used internally to determine if chart rendering should proceed.
        """
        return (
            len(self._market_data) > 0
            or len(self._strategy_data) > 0
            or any(self._plot_data.get(pt.value) for pt in PlotType)
        )

    def _unique_screens(self) -> List[int]:
        """
        Identify unique screen indices from plot data.

        Scans all plot data to find which screen indices are used,
        ensuring screen 0 (main chart) is always included.

        Returns:
            List[int]: Sorted list of screen indices (e.g., [0, 1, 2])

        Example:
            >>> # If plots use screen_index 0, 1, 2
            >>> canvas._unique_screens()
            [0, 1, 2]

        Note:
            Screen 0 is always included even if no plots explicitly use it,
            as it's reserved for the main price chart.
        """
        screens = {
            item.screen_index
            for plot_type in (PlotType.HISTOGRAM, PlotType.LINE, PlotType.AREA)
            for item in self._plot_data.get(plot_type.value, [])
        }
        screens.add(0)
        return sorted(screens)

    def convert_timestamp(self, timestamp) -> float:
        """
        Convert timestamp to matplotlib date number.

        Handles both string (ISO format) and datetime objects, converting
        them to matplotlib's internal date representation for plotting.

        Args:
            timestamp: Either datetime object or ISO format string

        Returns:
            float: Matplotlib date number

        Example:
            >>> ts_str = "2024-01-01T00:00:00+00:00"
            >>> num = canvas.convert_timestamp(ts_str)
            >>> # Use num for matplotlib plotting

        Note:
            Matplotlib uses a float-based date system where the integer
            part is days since 0001-01-01 UTC.
        """
        if isinstance(timestamp, str):
            return float(mdates.date2num(datetime.fromisoformat(timestamp)))
        return float(mdates.date2num(timestamp))

    def _create_figure_and_axes(
        self, screens: List[int], figsize: Tuple[float, float]
    ) -> Tuple[Any, Any]:
        """
        Create matplotlib figure and axes layout.

        Args:
            screens (List[int]): List of screen indices to create
            figsize (Tuple[float, float]): Figure size (width, height)

        Returns:
            Tuple[plt.Figure, Dict[int, plt.Axes]]: Figure and screen-to-axes mapping

        Note:
            Single screen creates one axis, multiple screens create
            vertically stacked subplots with shared x-axis.
        """
        unique_screens_count = len(screens)

        if unique_screens_count == 1:
            fig, ax = plt.subplots(figsize=figsize)
            axes = {screens[0]: ax}
        else:
            fig, axes_array = plt.subplots(
                unique_screens_count, 1, figsize=figsize, sharex=True, squeeze=False
            )
            axes_array = axes_array.flatten()
            axes = {screen_idx: axes_array[i] for i, screen_idx in enumerate(screens)}

        return fig, axes

    def _plot_histograms(self, axes: Any, histogram_alpha: float) -> None:
        """
        Render histogram plots on specified axes.

        Args:
            axes (Dict[int, plt.Axes]): Screen index to axes mapping
            histogram_alpha (float): Transparency level (0-1)

        Note:
            Automatically calculates bar width based on data density.
            Prevents duplicate legend entries for the same label.
        """
        plotted_histograms = set()

        for plot in self._plot_data.get(PlotType.HISTOGRAM.value, []):
            screen_idx = plot.screen_index

            if screen_idx not in axes:
                continue

            ax = axes[screen_idx]

            timestamps = [self.convert_timestamp(item.timestamp) for item in plot.data]
            values = [item.value for item in plot.data]

            bar_width = (
                (max(timestamps) - min(timestamps)) / len(timestamps) * 0.8
                if len(timestamps) > 1
                else 0.5
            )

            label = plot.label if plot.label not in plotted_histograms else "_nolegend_"
            plotted_histograms.add(plot.label)

            ax.bar(
                timestamps,
                values,
                label=label,
                color=self._get_color(plot.label),
                width=bar_width,
                alpha=histogram_alpha,
            )

    def _plot_lines(self, axes: Any, line_width: float) -> None:
        """
        Render line plots on specified axes.

        Args:
            axes (Dict[int, plt.Axes]): Screen index to axes mapping
            line_width (float): Line thickness

        Note:
            Used for indicators like moving averages, RSI, etc.
        """
        for plot in self._plot_data.get(PlotType.LINE.value, []):
            screen_idx = plot.screen_index
            if screen_idx not in axes:
                continue

            ax = axes[screen_idx]
            timestamps = [self.convert_timestamp(item.timestamp) for item in plot.data]
            values = [item.value for item in plot.data]

            ax.plot(
                timestamps,
                values,
                label=plot.label,
                color=self._get_color(plot.label),
                lw=line_width,
            )

    def _plot_areas(self, axes: Any, area_alpha: float) -> None:
        """
        Render area plots on specified axes.

        Args:
            axes (Dict[int, plt.Axes]): Screen index to axes mapping
            area_alpha (float): Transparency level (0-1)

        Note:
            Used for filled regions like Bollinger Bands, clouds, etc.
        """
        for plot in self._plot_data.get(PlotType.AREA.value, []):
            screen_idx = plot.screen_index
            if screen_idx not in axes:
                continue

            ax = axes[screen_idx]
            timestamps = [self.convert_timestamp(item.timestamp) for item in plot.data]
            values = [item.value for item in plot.data]

            ax.fill_between(
                timestamps,
                values,
                label=plot.label,
                color=self._get_color(plot.label),
                alpha=area_alpha,
            )

    def _build_candle_lookup_table(self) -> Dict[str, Tuple[float, float]]:
        """
        Build lookup table mapping timestamps to matplotlib coordinates and prices.

        Returns:
            Dict[str, Tuple[float, float]]: Map of ISO timestamp to (x_coord, price)

        Note:
            Used for positioning trading signal markers on the chart.
        """
        candle_lut = {}

        for item in self._market_data:
            timestamp = item.timestamp
            ts_str = timestamp if isinstance(timestamp, str) else timestamp.isoformat()
            ts_num = self.convert_timestamp(timestamp)
            price = item.close

            candle_lut[ts_str] = (ts_num, price)

        return candle_lut

    def _render_candlesticks(
        self, ax: Any, candle_linewidth: float, candle_body_width: float
    ) -> None:
        """
        Render OHLC candlestick chart.

        Args:
            ax (plt.Axes): Matplotlib axes to draw on
            candle_linewidth (float): Wick line width
            candle_body_width (float): Body line width

        Note:
            Green candles for up days (close > open)
            Red candles for down days (close < open)
        """
        for item in self._market_data:
            ts_num = self.convert_timestamp(item.timestamp)

            color = "green" if item.close > item.open else "red"

            ax.vlines(ts_num, item.low, item.high, color=color, lw=candle_linewidth)
            ax.vlines(ts_num, item.open, item.close, color=color, lw=candle_body_width)

    def _render_trading_signals(
        self,
        ax: Any,
        candle_lut: Dict[str, Tuple[float, float]],
        offset_multiplier: float,
        marker_size: int,
        annotation_fontsize: int,
    ) -> None:
        """
        Render trading signal markers and annotations.

        Args:
            ax (plt.Axes): Matplotlib axes to draw on
            candle_lut (Dict): Timestamp to coordinate mapping
            offset_multiplier (float): Marker offset as fraction of price
            marker_size (int): Size of marker triangles
            annotation_fontsize (int): Font size for annotations

        Note:
            LONG signals: Blue upward triangle below price
            SHORT signals: Purple downward triangle above price
        """
        for trade in self._strategy_data:
            ts_key = (
                trade.timestamp
                if isinstance(trade.timestamp, str)
                else trade.timestamp.isoformat()
            )

            if ts_key not in candle_lut:
                continue

            ts_num, price = candle_lut[ts_key]
            offset = price * offset_multiplier
            direction = trade.action
            amount = trade.amount

            if direction == ActionType.LONG:
                y = price - offset
                ax.plot(ts_num, y, marker="^", color="blue", markersize=marker_size)
                ax.annotate(
                    f"LONG {amount}",
                    xy=(ts_num, y),
                    xytext=(0, -15),
                    textcoords="offset points",
                    ha="center",
                    fontsize=annotation_fontsize,
                    color="blue",
                )

            elif direction == ActionType.SHORT:
                y = price + offset
                ax.plot(
                    ts_num,
                    y,
                    marker="v",
                    color="purple",
                    markersize=marker_size,
                )
                ax.annotate(
                    f"SHORT {amount}",
                    xy=(ts_num, y),
                    xytext=(0, 10),
                    textcoords="offset points",
                    ha="center",
                    fontsize=annotation_fontsize,
                    color="purple",
                )

    def _configure_main_chart(
        self,
        ax: Any,
        show_legend: bool,
        title: str,
        xlabel: str,
        ylabel: str,
        rotation: int,
        ha: str,
    ) -> None:
        """
        Configure main chart appearance and formatting.

        Args:
            ax (plt.Axes): Main chart axes
            show_legend (bool): Whether to display legend
            title (str): Chart title
            xlabel (str): X-axis label
            ylabel (str): Y-axis label
            rotation (int): X-axis label rotation angle
            ha (str): Horizontal alignment for x-axis labels

        Note:
            Automatically formats dates on x-axis and adds legend if requested.
        """
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.set_title(title)

        if show_legend and ax.get_legend_handles_labels()[0]:
            ax.legend()

        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=rotation, ha=ha)

    def _configure_subplots(self, axes: Any, show_legend: bool) -> None:
        """
        Configure additional subplot panels.

        Args:
            axes (Dict[int, plt.Axes]): Screen index to axes mapping
            show_legend (bool): Whether to display legends

        Note:
            Each subplot gets a label indicating its screen index.
        """
        for screen_idx, ax in axes.items():
            if screen_idx != 0:
                ax.set_ylabel(f"Screen {screen_idx}")
                if show_legend and ax.get_legend_handles_labels()[0]:
                    ax.legend()

    def draw(
        self,
        show_legend: bool = True,
        figsize: tuple = (12, 6),
        offset_multiplier: float = 0.05,
        rotation: int = 30,
        ha: str = "right",
        title: str = "Market Data Visualizations",
        xlabel: str = "Date",
        ylabel: str = "Price",
        candle_linewidth: float = 1,
        candle_body_width: float = 4,
        marker_size: int = 8,
        annotation_fontsize: int = 9,
        histogram_alpha: float = 0.6,
        area_alpha: float = 0.3,
        line_width: float = 2,
    ):
        """
        Render the complete financial chart.

        Creates a professional multi-panel chart with candlesticks,
        indicators, and trading signals. Automatically handles subplot
        layout based on screen indices used in plot data.

        Args:
            show_legend (bool): Whether to show the legend. Default True.
            figsize (tuple): Figure size as (width, height). Default (12, 6).
            offset_multiplier (float): Multiplier for trade annotation offset
                from price. Default 0.05 (5% of price).
            rotation (int): Rotation angle for x-axis labels. Default 30.
            ha (str): Horizontal alignment for x-axis labels ('left', 'center',
                'right'). Default 'right'.
            title (str): Chart title. Default 'Market Data Visualizations'.
            xlabel (str): X-axis label. Default 'Date'.
            ylabel (str): Y-axis label for main chart. Default 'Price'.
            candle_linewidth (float): Width of candlestick wick lines. Default 1.
            candle_body_width (float): Width of candlestick body lines. Default 4.
            marker_size (int): Size of trade signal markers. Default 8.
            annotation_fontsize (int): Font size for trade annotations. Default 9.
            histogram_alpha (float): Transparency for histogram bars (0-1).
                Default 0.6.
            area_alpha (float): Transparency for area plots (0-1). Default 0.3.
            line_width (float): Width of line plots. Default 2.

        Example:
            >>> # Basic usage
            >>> canvas.draw()
            >>>
            >>> # Customized for presentation
            >>> canvas.draw(
            ...     figsize=(16, 9),
            ...     title="Bitcoin Trading Strategy",
            ...     candle_body_width=6,
            ...     marker_size=12,
            ...     line_width=2.5
            ... )

        Note:
            - Screen 0 is reserved for the main price chart with candlesticks
            - Additional screens (1, 2, 3...) create separate subplot panels
            - Each subplot has its own y-axis scale
            - Long signals appear as blue upward triangles
            - Short signals appear as purple downward triangles
        """
        screens = self._unique_screens()
        unique_screens_count = len(screens)

        if unique_screens_count == 0:
            return

        fig, axes = self._create_figure_and_axes(screens, figsize)

        self._plot_histograms(axes, histogram_alpha)
        self._plot_lines(axes, line_width)
        self._plot_areas(axes, area_alpha)

        if 0 in axes:
            ax_main = axes[0]

            candle_lut = self._build_candle_lookup_table()

            self._render_candlesticks(ax_main, candle_linewidth, candle_body_width)

            self._render_trading_signals(
                ax_main,
                candle_lut,
                offset_multiplier,
                marker_size,
                annotation_fontsize,
            )

            self._configure_main_chart(
                ax_main, show_legend, title, xlabel, ylabel, rotation, ha
            )

        self._configure_subplots(axes, show_legend)

        if self._ctx.authenticated():
            output(self._ctx)

        plt.tight_layout()
        plt.show()
