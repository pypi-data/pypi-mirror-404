import unittest
from unittest.mock import Mock
from datetime import datetime, timezone

from openstoxlify.context import Context
from openstoxlify.models.enum import ActionType, PlotType, Period
from openstoxlify.models.series import ActionSeries, FloatSeries
from openstoxlify.models.model import Quote
from openstoxlify.models.contract import Provider


class TestContext(unittest.TestCase):
    """Test suite untuk Context class"""

    def setUp(self):
        """Setup mock provider dan context untuk setiap test"""
        self.mock_provider = Mock(spec=Provider)
        self.symbol = "BTC-USD"
        self.period = Period.DAILY
        self.ctx = Context(
            ["file.py", "token", "id"], self.mock_provider, self.symbol, self.period
        )

    def test_initialization(self):
        """Test apakah Context di-initialize dengan benar"""
        self.assertEqual(self.ctx.symbol(), self.symbol)
        self.assertEqual(self.ctx.period(), self.period)
        self.assertEqual(self.ctx.provider(), self.mock_provider)
        self.assertFalse(self.ctx._authenticated)
        self.assertEqual(self.ctx._token, "token")

    def test_quotes_first_call(self):
        """Test quotes() memanggil provider saat pertama kali"""
        mock_quotes = [
            Quote(
                timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc),
                high=100.0,
                low=90.0,
                open=95.0,
                close=98.0,
                volume=1000,
            ),
            Quote(
                timestamp=datetime(2024, 1, 2, tzinfo=timezone.utc),
                high=105.0,
                low=95.0,
                open=98.0,
                close=102.0,
                volume=1500,
            ),
        ]
        self.mock_provider.quotes.return_value = mock_quotes

        result = self.ctx.quotes()

        self.mock_provider.quotes.assert_called_once_with(
            self.symbol, self.period, None, None
        )
        self.assertEqual(result, mock_quotes)
        self.assertEqual(len(result), 2)

    def test_quotes_cached(self):
        """Test quotes() menggunakan cache setelah pemanggilan pertama"""
        mock_quotes = [
            Quote(
                timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc),
                high=100.0,
                low=90.0,
                open=95.0,
                close=98.0,
                volume=1000,
            )
        ]
        self.mock_provider.quotes.return_value = mock_quotes

        # First call
        result1 = self.ctx.quotes()
        # Second call
        result2 = self.ctx.quotes()

        # Provider should only be called once
        self.mock_provider.quotes.assert_called_once()
        self.assertEqual(result1, result2)

    def test_plot_line_new_label(self):
        """Test plot() menambahkan data baru dengan label baru"""
        timestamp = datetime(2024, 1, 1, tzinfo=timezone.utc)
        data = FloatSeries(timestamp, 100.0)

        self.ctx.plot("MA20", PlotType.LINE, data)

        plots = self.ctx.plots()
        self.assertIn(PlotType.LINE.value, plots)
        self.assertEqual(len(plots[PlotType.LINE.value]), 1)
        self.assertEqual(plots[PlotType.LINE.value][0].label, "MA20")
        self.assertEqual(len(plots[PlotType.LINE.value][0].data), 1)

    def test_plot_line_existing_label(self):
        """Test plot() menambahkan data ke label yang sudah ada"""
        timestamp1 = datetime(2024, 1, 1, tzinfo=timezone.utc)
        timestamp2 = datetime(2024, 1, 2, tzinfo=timezone.utc)
        data1 = FloatSeries(timestamp1, 100.0)
        data2 = FloatSeries(timestamp2, 105.0)

        self.ctx.plot("MA20", PlotType.LINE, data1)
        self.ctx.plot("MA20", PlotType.LINE, data2)

        plots = self.ctx.plots()
        self.assertEqual(len(plots[PlotType.LINE.value]), 1)
        self.assertEqual(len(plots[PlotType.LINE.value][0].data), 2)

    def test_plot_multiple_screens(self):
        """Test plot() dengan multiple screen indices"""
        timestamp = datetime(2024, 1, 1, tzinfo=timezone.utc)
        data1 = FloatSeries(timestamp, 100.0)
        data2 = FloatSeries(timestamp, 50.0)

        self.ctx.plot("Price", PlotType.LINE, data1, screen_index=0)
        self.ctx.plot("MACD", PlotType.HISTOGRAM, data2, screen_index=1)

        plots = self.ctx.plots()
        self.assertEqual(plots[PlotType.LINE.value][0].screen_index, 0)
        self.assertEqual(plots[PlotType.HISTOGRAM.value][0].screen_index, 1)

    def test_signal_long_action(self):
        """Test signal() dengan LONG action"""
        timestamp = datetime(2024, 1, 1, tzinfo=timezone.utc)
        signal = ActionSeries(timestamp, ActionType.LONG, 1.5)

        self.ctx.signal(signal)

        signals = self.ctx.signals()
        self.assertEqual(len(signals), 1)
        self.assertEqual(signals[0].action, ActionType.LONG)
        self.assertEqual(signals[0].amount, 1.5)

    def test_signal_hold_action_resets_amount(self):
        """Test signal() dengan HOLD action mengeset amount ke 0"""
        timestamp = datetime(2024, 1, 1, tzinfo=timezone.utc)
        signal = ActionSeries(timestamp, ActionType.HOLD, 5.0)

        self.ctx.signal(signal)

        signals = self.ctx.signals()
        self.assertEqual(signals[0].amount, 0.0)

    def test_authenticate_success(self):
        """Test authenticate() berhasil"""
        self.mock_provider.authenticate.return_value = None

        self.ctx.authenticate()

        self.assertTrue(self.ctx._authenticated)

    def test_authenticate_failure(self):
        """Test authenticate() gagal"""
        self.mock_provider.authenticate.side_effect = Exception("Auth failed")

        self.ctx.authenticate()

        self.assertFalse(self.ctx._authenticated)

    def test_execute_not_authenticated(self):
        """Test execute() tidak berjalan jika tidak authenticated"""
        self.ctx.execute()

        self.mock_provider.execute.assert_not_called()

    def test_execute_no_signal_at_latest_timestamp(self):
        """Test execute() tidak berjalan jika tidak ada signal di timestamp terbaru"""
        self.ctx._authenticated = True
        self.ctx._quotes = [
            Quote(
                timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc),
                high=100.0,
                low=90.0,
                open=95.0,
                close=98.0,
                volume=1000,
            ),
            Quote(
                timestamp=datetime(2024, 1, 2, tzinfo=timezone.utc),
                high=105.0,
                low=95.0,
                open=98.0,
                close=102.0,
                volume=1500,
            ),
        ]

        signal = ActionSeries(
            datetime(2024, 1, 1, tzinfo=timezone.utc), ActionType.LONG, 1.0
        )
        self.ctx.signal(signal)

        self.ctx.execute()

        self.mock_provider.execute.assert_not_called()

    def test_execute_with_hold_signal(self):
        """Test execute() tidak execute jika signal adalah HOLD"""
        self.ctx._authenticated = True
        timestamp = datetime(2024, 1, 2, tzinfo=timezone.utc)

        self.ctx._quotes = [
            Quote(
                timestamp=timestamp,
                high=100.0,
                low=90.0,
                open=95.0,
                close=98.0,
                volume=1000,
            )
        ]

        signal = ActionSeries(timestamp, ActionType.HOLD, 0.0)
        self.ctx.signal(signal)

        self.ctx.execute()

        self.mock_provider.execute.assert_not_called()

    def test_execute_with_valid_signal(self):
        """Test execute() berhasil dengan signal yang valid"""
        self.ctx._authenticated = True
        timestamp = datetime(2024, 1, 2, tzinfo=timezone.utc)

        self.ctx._quotes = [
            Quote(
                timestamp=timestamp,
                high=100.0,
                low=90.0,
                open=95.0,
                close=98.0,
                volume=1000,
            )
        ]

        signal = ActionSeries(timestamp, ActionType.LONG, 2.5)
        self.ctx.signal(signal)

        self.ctx.authenticate()
        self.ctx.execute()

        self.mock_provider.execute.assert_called_once_with(
            "id", self.symbol, signal, 2.5
        )


if __name__ == "__main__":
    unittest.main()
