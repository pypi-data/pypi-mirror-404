import unittest
from unittest.mock import Mock, patch
from datetime import datetime, timezone

from openstoxlify.context import Context
from openstoxlify.draw import Canvas
from openstoxlify.models.enum import ActionType, PlotType, Period
from openstoxlify.models.series import ActionSeries, FloatSeries
from openstoxlify.models.model import Quote
from openstoxlify.models.contract import Provider


class TestIntegration(unittest.TestCase):
    """Integration tests untuk workflow lengkap"""

    def setUp(self):
        """Setup untuk integration tests"""
        self.mock_provider = Mock(spec=Provider)
        self.symbol = "BTC-USD"
        self.period = Period.DAILY

    def test_full_workflow_simple(self):
        """Test workflow sederhana: get quotes, plot, signal"""
        mock_quotes = [
            Quote(
                timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc),
                high=105.0,
                low=95.0,
                open=100.0,
                close=102.0,
                volume=1000,
            ),
            Quote(
                timestamp=datetime(2024, 1, 2, tzinfo=timezone.utc),
                high=110.0,
                low=100.0,
                open=102.0,
                close=108.0,
                volume=1500,
            ),
            Quote(
                timestamp=datetime(2024, 1, 3, tzinfo=timezone.utc),
                high=115.0,
                low=105.0,
                open=108.0,
                close=98.0,
                volume=2000,
            ),
        ]
        self.mock_provider.quotes.return_value = mock_quotes

        ctx = Context(
            ["file.py", "token", "id"], self.mock_provider, self.symbol, self.period
        )

        quotes = ctx.quotes()
        self.assertEqual(len(quotes), 3)

        from statistics import median

        prices = [q.close for q in quotes]
        median_value = median(prices)

        for quote in quotes:
            ctx.plot(
                "Median", PlotType.LINE, FloatSeries(quote.timestamp, median_value)
            )

        lowest = min(quotes, key=lambda q: q.close)
        highest = max(quotes, key=lambda q: q.close)

        ctx.signal(ActionSeries(lowest.timestamp, ActionType.LONG, 1.0))
        ctx.signal(ActionSeries(highest.timestamp, ActionType.SHORT, 1.0))

        plots = ctx.plots()
        signals = ctx.signals()

        self.assertIn(PlotType.LINE.value, plots)
        self.assertEqual(len(plots[PlotType.LINE.value][0].data), 3)
        self.assertEqual(len(signals), 2)
        self.assertEqual(signals[0].action, ActionType.LONG)
        self.assertEqual(signals[1].action, ActionType.SHORT)

    @patch("openstoxlify.draw.plt.subplots")
    @patch("openstoxlify.draw.plt.show")
    def test_full_workflow_with_canvas(self, mock_show, mock_subplots):
        """Test workflow lengkap dengan Canvas"""
        mock_fig = Mock()
        mock_ax = Mock()
        mock_ax.get_legend_handles_labels.return_value = ([], [])
        mock_ax.xaxis = Mock()
        mock_ax.xaxis.get_majorticklabels.return_value = []
        mock_ax.xaxis.set_major_locator = Mock()
        mock_ax.xaxis.set_major_formatter = Mock()
        mock_subplots.return_value = (mock_fig, mock_ax)

        mock_quotes = [
            Quote(
                timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc),
                high=105.0,
                low=95.0,
                open=100.0,
                close=102.0,
                volume=1000,
            )
        ]
        self.mock_provider.quotes.return_value = mock_quotes

        ctx = Context(
            ["file.py", "token", "id"], self.mock_provider, self.symbol, self.period
        )
        quotes = ctx.quotes()

        for quote in quotes:
            ctx.plot("Price", PlotType.LINE, FloatSeries(quote.timestamp, quote.close))

        ctx.signal(ActionSeries(quotes[0].timestamp, ActionType.LONG, 1.0))

        canvas = Canvas(ctx)
        canvas.draw()

        mock_show.assert_called_once()


if __name__ == "__main__":
    unittest.main()
