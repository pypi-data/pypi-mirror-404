# OpenStoxlify 📈

[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/michaelahli/openstoxlify)
[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![LLM Spec](https://img.shields.io/badge/LLM%20SPEC-purple?logo=ollama)](AGENTS.md)

A lightweight Python library for algorithmic trading and market analysis with professional-grade visualizations.

---

## ✨ Key Features

- **Multi-source data**: Fetch from Yahoo Finance, Binance, and more via gRPC
- **Context-based API**: Clean, fluent interface for strategy development
- **Strategy engine**: Record and visualize trading signals
- **Professional charts**: OHLC candles, indicators, and strategy markers
- **Live trading**: Authentication and execution support for automated trading
- **Flexible outputs**: Interactive plots and JSON exports

---

## 🚀 Quick Start

```python
import sys
from openstoxlify.context import Context
from openstoxlify.draw import Canvas
from openstoxlify.providers.stoxlify.provider import Provider
from openstoxlify.models.enum import ActionType, DefaultProvider, Period, PlotType
from openstoxlify.models.series import ActionSeries, FloatSeries

# 1. Initialize provider and context
provider = Provider(DefaultProvider.YFinance)
ctx = Context(sys.argv, provider, "AAPL", Period.DAILY)

# 2. Get market data
quotes = ctx.quotes()

# 3. Plot closing prices
for quote in quotes:
    ctx.plot("Close", PlotType.LINE, FloatSeries(quote.timestamp, quote.close))

# 4. Add trading signals
ctx.signal(ActionSeries(quotes[0].timestamp, ActionType.LONG, 1.0))

# 5. Visualize
canvas = Canvas(ctx)
canvas.draw()

# 6. (Optional) Live trading - requires authentication
ctx.authenticate()
ctx.execute()
```

---

## 📦 Installation

### Basic Installation

```bash
pip install openstoxlify
```

### For Development

```bash
git clone https://github.com/michaelahli/openstoxlify.git
cd openstoxlify
make clean setup
source .venv/bin/activate  # or `venv/bin/activate`
python examples/getting_started.py
```

### Requirements

| Package    | Minimum Version | Notes                           |
| ---------- | --------------- | ------------------------------- |
| Python     | 3.8+            |                                 |
| grpcio     | 1.50+           | For data provider communication |
| matplotlib | 3.5+            | Required for visualization      |
| protobuf   | 4.0+            | For protocol buffers            |
| utcnow     | Latest          | For timestamp handling          |

### Troubleshooting

1. **Missing Dependencies**:

   ```bash
   pip install --upgrade grpcio matplotlib protobuf utcnow
   ```

2. **Permission Issues** (Linux/Mac):

   ```bash
   pip install --user openstoxlify
   ```

3. **Conda Users**:

   ```bash
   conda install -c conda-forge grpcio matplotlib
   pip install openstoxlify
   ```

---

## 📊 Core Components

### 1. Context - The Trading Context Manager

The `Context` class is the heart of OpenStoxlify. It manages your market data, plots, and trading signals in one place.

```python
import sys
from openstoxlify.context import Context
from openstoxlify.providers.stoxlify.provider import Provider
from openstoxlify.models.enum import DefaultProvider, Period

# Initialize provider
provider = Provider(DefaultProvider.YFinance)

# Create trading context
ctx = Context(
    agrv=sys.argv,           # Command-line arguments
    provider=provider,
    symbol="BTC-USD",
    period=Period.DAILY
)
```

**Context Methods**:

| Method                  | Description                       | Returns         |
| ----------------------- | --------------------------------- | --------------- |
| `quotes()`              | Get market data (cached)          | `List[Quote]`   |
| `plot(label, type, data, screen_index)` | Add plot data | `None`          |
| `signal(action_series)` | Record trading signal             | `None`          |
| `authenticate()`        | Authenticate with provider token  | `None`          |
| `execute(offset=0)`     | Execute latest trading signal     | `None`          |
| `plots()`               | Get all plot data                 | `Dict`          |
| `signals()`             | Get all trading signals           | `List`          |
| `symbol()`              | Get current trading symbol        | `str`           |
| `period()`              | Get current timeframe             | `Period`        |
| `provider()`            | Get provider instance             | `Provider`      |
| `authenticated()`       | Check authentication status       | `bool`          |
| `id()`                  | Get context unique identifier     | `str \| None`   |

---

### 2. Providers - Custom Data Sources

**Provider Protocol**:

OpenStoxlify uses a protocol-based provider system, allowing you to implement your own data sources. Any class that implements the `Provider` protocol will work:

```python
from typing import List, Protocol
from openstoxlify.models.model import Quote
from openstoxlify.models.enum import Period
from openstoxlify.models.series import ActionSeries

@runtime_checkable
class Provider(Protocol):
    def source(self) -> str:
        """Return provider name/identifier"""
        ...
    
    def quotes(self, symbol: str, period: Period, start: datetime | None = None, end: datetime | None = None) -> List[Quote]:
        """Fetch OHLCV market data"""
        ...
    
    def authenticate(self, token: str) -> None:
        """Authenticate with provider (optional for live trading)"""
        ...
    
    def execute(self, id: str, symbol: str, action: ActionSeries, amount: float) -> None:
        """Execute trade (optional for live trading)"""
        ...
```

**Built-in Stoxlify Provider**:

The included `stoxlify.provider.Provider` is just one implementation using gRPC:

```python
from openstoxlify.providers.stoxlify.provider import Provider
from openstoxlify.models.enum import DefaultProvider

# Using built-in provider
provider = Provider(DefaultProvider.YFinance)  # Yahoo Finance
provider = Provider(DefaultProvider.Binance)   # Binance (crypto)
```

**Implement Your Own Provider**:

```python
from typing import List
from openstoxlify.models.model import Quote
from openstoxlify.models.enum import Period
from openstoxlify.models.series import ActionSeries

class MyCustomProvider:
    def source(self) -> str:
        return "MyDataSource"
    
    def quotes(self, symbol: str, period: Period, start: datetime | None = None, end: datetime | None = None) -> List[Quote]:
        # Fetch from your API, database, CSV, etc.
        # Must return List[Quote] with UTC timestamps
        return my_fetch_logic(symbol, period)
    
    def authenticate(self, token: str) -> None:
        # Optional: implement if you need authentication
        self.api_key = token
    
    def execute(self, id: str, symbol: str, action: ActionSeries, amount: float) -> None:
        # Optional: implement if you support live trading
        pass

# Use your custom provider
provider = MyCustomProvider()
ctx = Context(sys.argv, provider, "AAPL", Period.DAILY)
```

**Available Timeframes**:

| Period          | Interval | Description        |
| --------------- | -------- | ------------------ |
| `Period.MINUTELY`   | 1m       | 1-minute candles   |
| `Period.QUINTLY`    | 5m       | 5-minute candles   |
| `Period.HALFHOURLY` | 30m      | 30-minute candles  |
| `Period.HOURLY`     | 60m      | 1-hour candles     |
| `Period.DAILY`      | D        | Daily candles      |
| `Period.WEEKLY`     | W        | Weekly candles     |
| `Period.MONTHLY`    | M        | Monthly candles    |

**Example with Custom Provider**:

```python
import sys
from openstoxlify.context import Context
from openstoxlify.models.enum import Period

# Your custom implementation
provider = MyCustomProvider()
ctx = Context(sys.argv, provider, "BTCUSDT", Period.HOURLY)
quotes = ctx.quotes()
```

**Provider Requirements**:

- Must implement the `Provider` protocol (see `models/contract.py`)
- `quotes()` must return `List[Quote]` with timezone-aware UTC timestamps
- `authenticate()` and `execute()` are optional (only needed for live trading)
- You can fetch data from any source: REST APIs, databases, CSV files, websockets, etc.

---

### 3. Plotting - Visualize Indicators

Plot technical indicators alongside market data:

```python
from openstoxlify.models.enum import PlotType
from openstoxlify.models.series import FloatSeries

# Plot a single data point
ctx.plot(
    label="SMA 20",              # Indicator name
    plot_type=PlotType.LINE,     # Plot style
    data=FloatSeries(
        timestamp=quote.timestamp,
        value=sma_value
    ),
    screen_index=0               # Main chart (0) or subplot (1, 2, ...)
)
```

**Plot Types**:

| Type                | Description              | Use Case                     |
| ------------------- | ------------------------ | ---------------------------- |
| `PlotType.LINE`     | Continuous line          | Moving averages, price lines |
| `PlotType.HISTOGRAM`| Vertical bars            | Volume, MACD histogram       |
| `PlotType.AREA`     | Filled area under curve  | Bollinger Bands, clouds      |
| `PlotType.CANDLESTICK` | OHLC candles          | Price action (internal)      |

**Multi-Screen Layouts**:

```python
# Main chart (screen 0)
ctx.plot("Price", PlotType.LINE, FloatSeries(ts, price), screen_index=0)
ctx.plot("SMA 20", PlotType.LINE, FloatSeries(ts, sma20), screen_index=0)

# MACD subplot (screen 1)
ctx.plot("MACD", PlotType.HISTOGRAM, FloatSeries(ts, macd), screen_index=1)

# RSI subplot (screen 2)
ctx.plot("RSI", PlotType.LINE, FloatSeries(ts, rsi), screen_index=2)
```

---

### 4. Trading Signals

Record buy/sell decisions:

```python
from openstoxlify.models.enum import ActionType
from openstoxlify.models.series import ActionSeries

# Record a LONG (buy) signal
ctx.signal(ActionSeries(
    timestamp=quote.timestamp,
    action=ActionType.LONG,
    amount=1.5  # Position size
))

# Record a SHORT (sell) signal
ctx.signal(ActionSeries(
    timestamp=quote.timestamp,
    action=ActionType.SHORT,
    amount=2.0
))

# Record a HOLD (no action)
ctx.signal(ActionSeries(
    timestamp=quote.timestamp,
    action=ActionType.HOLD,
    amount=0.0  # Amount is automatically set to 0 for HOLD
))
```

**Action Types**:

| Type                | Description           | Visual Marker    |
| ------------------- | --------------------- | ---------------- |
| `ActionType.LONG`   | Buy/Bullish position  | ▲ Blue arrow     |
| `ActionType.SHORT`  | Sell/Bearish position | ▼ Purple arrow   |
| `ActionType.HOLD`   | No action             | (not displayed)  |

---

### 5. Canvas - Render Charts

The `Canvas` class generates professional financial charts:

```python
from openstoxlify.draw import Canvas

# Create canvas from context
canvas = Canvas(ctx)

# Draw with default settings
canvas.draw()

# Draw with custom styling
canvas.draw(
    show_legend=True,
    figsize=(16, 9),
    title="My Trading Strategy",
    candle_linewidth=1.5,
    marker_size=10
)
```

---

## 🎨 Visualization with `draw()`

### Basic Usage

```python
import sys
from openstoxlify.context import Context
from openstoxlify.draw import Canvas
from openstoxlify.providers.stoxlify.provider import Provider
from openstoxlify.models.enum import DefaultProvider, Period

provider = Provider(DefaultProvider.YFinance)
ctx = Context(sys.argv, provider, "AAPL", Period.DAILY)

# Add your plots and signals...

canvas = Canvas(ctx)
canvas.draw()  # Displays interactive matplotlib chart
```

### Full Customization Example

```python
canvas.draw(
    show_legend=True,             # Toggle legend visibility
    figsize=(16, 9),              # Larger figure size
    offset_multiplier=0.03,       # Adjust trade marker positions
    rotation=45,                  # X-axis label rotation
    ha='right',                   # Horizontal alignment
    title="Custom Strategy Backtest",
    xlabel="Trading Days",
    ylabel="Price (USD)",
    candle_linewidth=0.8,         # Wick thickness
    candle_body_width=3,          # Body thickness
    marker_size=10,               # Trade signal markers
    annotation_fontsize=8,        # Trade annotation text
    histogram_alpha=0.7,          # Histogram transparency
    area_alpha=0.4,               # Area plot transparency
    line_width=2.5                # Trend line thickness
)
```

### Chart Features

| Element          | Description                         | Example Visual    |
| ---------------- | ----------------------------------- | ----------------- |
| **Candlesticks** | Green/red based on price direction  | 🟩🟥                |
| **Signals**      | Annotated markers for trades        | ▲ LONG<br>▼ SHORT |
| **Indicators**   | Lines, histograms, and filled areas | ━━━━━             |

### Example Output

![Sample Chart](public/images/ma_chart.png)

### Key Parameters

| Parameter             | Type  | Default                      | Description                       |
| --------------------- | ----- | ---------------------------- | --------------------------------- |
| `show_legend`         | bool  | True                         | Show/hide chart legend            |
| `figsize`             | tuple | (12, 6)                      | Figure dimensions (width, height) |
| `offset_multiplier`   | float | 0.05                         | Trade marker offset from price    |
| `rotation`            | int   | 30                           | X-axis label rotation angle       |
| `ha`                  | str   | 'right'                      | X-axis label horizontal alignment |
| `title`               | str   | "Market Data Visualizations" | Chart title                       |
| `xlabel`              | str   | "Date"                       | X-axis label                      |
| `ylabel`              | str   | "Price"                      | Y-axis label                      |
| `candle_linewidth`    | float | 1                            | Candlestick wick line width       |
| `candle_body_width`   | float | 4                            | Candlestick body line width       |
| `marker_size`         | int   | 8                            | Trade marker size                 |
| `annotation_fontsize` | int   | 9                            | Trade annotation font size        |
| `histogram_alpha`     | float | 0.6                          | Histogram bar transparency        |
| `area_alpha`          | float | 0.3                          | Area plot transparency            |
| `line_width`          | float | 2                            | Line plot width                   |

---

## 📚 Complete Examples

### 1. Simple Trading Strategy (from `getting_started.py`)

```python
import sys
from statistics import median
from openstoxlify.context import Context
from openstoxlify.draw import Canvas
from openstoxlify.providers.stoxlify.provider import Provider
from openstoxlify.models.enum import ActionType, DefaultProvider, Period, PlotType
from openstoxlify.models.series import ActionSeries, FloatSeries

# Setup
provider = Provider(DefaultProvider.YFinance)
ctx = Context(sys.argv, provider, "BTC-USD", Period.DAILY)

# Get market data
quotes = ctx.quotes()

# Calculate median price
prices = [quote.close for quote in quotes]
median_value = median(prices)

# Find extremes
lowest = min(quotes, key=lambda q: q.close)
highest = max(quotes, key=lambda q: q.close)

# Plot median line
for quote in quotes:
    ctx.plot("Median", PlotType.LINE, FloatSeries(quote.timestamp, median_value))

# Add signals at extremes
ctx.signal(ActionSeries(lowest.timestamp, ActionType.LONG, 1))
ctx.signal(ActionSeries(highest.timestamp, ActionType.SHORT, 1))

# Visualize
canvas = Canvas(ctx)
canvas.draw()

# Optional: Live trading (requires authentication token via command line)
ctx.authenticate()
ctx.execute()
```

### 2. Multi-Indicator Strategy (from `subplots.py`)

```python
import sys
from openstoxlify.context import Context
from openstoxlify.draw import Canvas
from openstoxlify.providers.stoxlify.provider import Provider
from openstoxlify.models.enum import ActionType, DefaultProvider, Period, PlotType
from openstoxlify.models.series import ActionSeries, FloatSeries

provider = Provider(DefaultProvider.YFinance)
ctx = Context(sys.argv, provider, "BTC-USD", Period.DAILY)
market_data = ctx.quotes()

# Helper functions
def calculate_average(market_data, window):
    prices = [q.close for q in market_data]
    return [
        (market_data[i + window - 1].timestamp, sum(prices[i:i + window]) / window)
        for i in range(len(prices) - window + 1)
    ]

def calculate_macd(market_data, fast_period, slow_period, signal_period):
    closes = [q.close for q in market_data]
    fast = [sum(closes[i:i+fast_period])/fast_period for i in range(len(closes)-fast_period+1)]
    slow = [sum(closes[i:i+slow_period])/slow_period for i in range(len(closes)-slow_period+1)]
    macd_line = [f - s for f, s in zip(fast, slow)]
    signal_line = [sum(macd_line[i:i+signal_period])/signal_period 
                   for i in range(len(macd_line)-signal_period+1)]
    histogram = [m - s for m, s in zip(macd_line[-len(signal_line):], signal_line)]
    timestamps = [market_data[i].timestamp 
                  for i in range(slow_period+signal_period-2, len(closes))]
    return [(t, h) for t, h in zip(timestamps, histogram)]

def calculate_stochastic(market_data, period):
    results = []
    for i in range(period - 1, len(market_data)):
        high_range = max(q.high for q in market_data[i-period+1:i+1])
        low_range = min(q.low for q in market_data[i-period+1:i+1])
        close = market_data[i].close
        value = 100 * ((close - low_range) / (high_range - low_range)) if high_range != low_range else 50
        results.append((market_data[i].timestamp, value))
    return results

# Calculate indicators
ma_fast = calculate_average(market_data, 20)
ma_slow = calculate_average(market_data, 50)
macd_hist = calculate_macd(market_data, 12, 26, 9)
stochastic = calculate_stochastic(market_data, 14)

# Plot price and indicators
for q in market_data:
    ctx.plot("Price", PlotType.LINE, FloatSeries(q.timestamp, q.close))

for t, v in ma_fast:
    ctx.plot("MA 20", PlotType.LINE, FloatSeries(t, v))

for t, v in ma_slow:
    ctx.plot("MA 50", PlotType.LINE, FloatSeries(t, v))

for t, v in macd_hist:
    ctx.plot("MACD Histogram", PlotType.HISTOGRAM, FloatSeries(t, v), 1)

for t, v in stochastic:
    ctx.plot("Stochastic", PlotType.LINE, FloatSeries(t, v), 2)

# Generate signals based on multiple indicators
ma_fast_dict = dict(ma_fast)
ma_slow_dict = dict(ma_slow)
macd_dict = dict(macd_hist)
stoch_dict = dict(stochastic)

for q in market_data:
    ts = q.timestamp
    if all(ts in d for d in [ma_fast_dict, ma_slow_dict, macd_dict, stoch_dict]):
        if ma_fast_dict[ts] > ma_slow_dict[ts] and macd_dict[ts] > 0 and stoch_dict[ts] < 20:
            ctx.signal(ActionSeries(ts, ActionType.LONG, 1))
        elif ma_fast_dict[ts] < ma_slow_dict[ts] and macd_dict[ts] < 0 and stoch_dict[ts] > 80:
            ctx.signal(ActionSeries(ts, ActionType.SHORT, 1))

# Visualize
canvas = Canvas(ctx)
canvas.draw()
```

---

## 🔐 Authentication & Execution

### Command-Line Token Passing

For live trading with supported providers, pass authentication tokens via command-line arguments:

```bash
python my_strategy.py YOUR_API_TOKEN YOUR_ID
```

### In Your Code

```python
import sys
from openstoxlify.context import Context

# Context automatically extracts token and id from sys.argv
ctx = Context(sys.argv, provider, "AAPL", Period.DAILY)

# Authenticate (validates token with provider)
ctx.authenticate()

# Execute the latest signal
ctx.execute()  # Only executes if authenticated

# Or execute at specific offset
ctx.execute(offset=1)  # Execute at second-to-last candle
```

**Execution Requirements**:

The `execute()` method will only run if:

1. Context is authenticated (`ctx.authenticated() == True`)
2. There's a signal at the target timestamp
3. The signal is not `ActionType.HOLD`
4. Valid token and ID are provided

---

## 📖 API Reference

### Data Structures

#### Quote

```python
@dataclass
class Quote:
    timestamp: datetime  # Time of measurement (timezone-aware UTC)
    high: float          # Period high price
    low: float           # Period low price
    open: float          # Opening price
    close: float         # Closing price
    volume: float        # Trading volume
```

#### FloatSeries

```python
@dataclass
class FloatSeries:
    timestamp: datetime  # Data point time
    value: float         # Indicator value
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON export"""
```

#### ActionSeries

```python
@dataclass
class ActionSeries:
    timestamp: datetime  # Signal time
    action: ActionType   # LONG, SHORT, or HOLD
    amount: float        # Position size (default 0.0)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON export"""
```

#### PlotData

```python
@dataclass
class PlotData:
    label: str                    # Indicator name
    data: List[FloatSeries]       # Time series data
    screen_index: int             # Subplot panel (0 = main)
```

---

## 🤖 LLM Usage & AI Code Generation

OpenStoxlify supports AI-generated trading strategies.

For **strict rules, canonical patterns, and forbidden behaviors**
that LLMs must follow when generating OpenStoxlify code, see:

👉 **AGENTS.md**

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

MIT © 2026 OpenStoxlify

---

## 🔗 Links

- [Documentation](https://github.com/michaelahli/openstoxlify/wiki)
- [Examples](https://github.com/michaelahli/openstoxlify/tree/main/examples)
- [Issue Tracker](https://github.com/michaelahli/openstoxlify/issues)
- [DeepWiki](https://deepwiki.com/michaelahli/openstoxlify)

---

## ⭐ Support

If you find this library helpful, please consider giving it a star on GitHub!
