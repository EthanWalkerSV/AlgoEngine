# AlgoEngine API Reference

Complete API documentation for the AlgoEngine algorithmic trading platform.

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Core Modules](#core-modules)
  - [Data Models](#data-models)
  - [Trading](#trading)
  - [Portfolio](#portfolio)
  - [Risk Management](#risk-management)
  - [Algorithms](#algorithms)
  - [Backtesting](#backtesting)
- [Examples](#examples)

---

## Installation

```bash
pip install -e .
```

### Dependencies

```bash
pip install numpy pandas pytz aiohttp yfinance
```

Optional for storage:
```bash
pip install pyarrow  # For Parquet storage
```

---

## Quick Start

```python
from decimal import Decimal
from datetime import datetime, timedelta
from src.backtesting.engine import BacktestEngine, BacktestConfig
from src.algorithms.sample_strategies import SMAStrategy
from src.data.models import Symbol, Bar, Resolution

# 1. Configure backtest
config = BacktestConfig(
    start_date=datetime(2023, 1, 1),
    end_date=datetime(2023, 12, 31),
    symbols=[Symbol(ticker="AAPL")],
    initial_cash=Decimal("100000.00")
)

# 2. Create engine
engine = BacktestEngine(config)

# 3. Load historical data
bars = [...]  # List of Bar objects
engine.load_historical_data(Symbol(ticker="AAPL"), bars)

# 4. Register and add strategy
engine.register_strategy("SMA", SMAStrategy)
strategy = engine.add_strategy("SMA", {"fast_period": 10, "slow_period": 30})

# 5. Run backtest
import asyncio
results = asyncio.run(engine.run())

# 6. View results
results.print_report()
```

---

## Core Modules

### Data Models

#### Symbol

Represents a financial instrument.

```python
from src.data.models import Symbol, SecurityType

# Create a stock symbol
symbol = Symbol(
    ticker="AAPL",
    security_type=SecurityType.EQUITY,
    exchange="NASDAQ",
    currency="USD"
)

# String representation
print(symbol)  # "AAPL"
print(symbol.ticker)  # "AAPL"
```

#### Bar

OHLCV bar data.

```python
from src.data.models import Bar
from decimal import Decimal
from datetime import datetime

bar = Bar(
    symbol=symbol,
    timestamp=datetime.now(),
    open=Decimal("150.00"),
    high=Decimal("155.00"),
    low=Decimal("149.00"),
    close=Decimal("152.50"),
    volume=1000000,
    resolution=Resolution.MINUTE
)
```

#### Tick

Real-time tick data.

```python
from src.data.models import Tick

tick = Tick(
    symbol=symbol,
    timestamp=datetime.now(),
    price=Decimal("152.50"),
    size=Decimal("100"),
    bid=Decimal("152.49"),
    ask=Decimal("152.51")
)
```

---

### Trading

#### Order

Create and manage orders.

```python
from src.trading.models import Order, OrderSide, OrderType, TimeInForce
from decimal import Decimal

# Market order
order = Order(
    symbol=symbol,
    side=OrderSide.BUY,
    quantity=Decimal("100"),
    order_type=OrderType.MARKET,
    time_in_force=TimeInForce.DAY
)

# Limit order
limit_order = Order(
    symbol=symbol,
    side=OrderSide.BUY,
    quantity=Decimal("100"),
    order_type=OrderType.LIMIT,
    limit_price=Decimal("150.00")
)

# Check order status
print(order.status)  # OrderStatus.SUBMITTED
print(order.is_active)  # True
print(order.filled_quantity)  # 0
```

#### OrderManager

Manage order lifecycle.

```python
from src.trading.order_manager import OrderManager

manager = OrderManager()

# Register order
manager.register_order(order)

# Get order
retrieved = manager.get_order(order.order_id)

# Cancel order
manager.cancel_order(order.order_id)

# Cancel all orders
cancelled_count = manager.cancel_all_orders()

# Set callbacks
manager.on_order(lambda o: print(f"Order: {o.order_id}"))
manager.on_fill(lambda f: print(f"Fill: {f.fill_id}"))
```

#### PositionManager

Track positions and calculate P&L.

```python
from src.trading.position_manager import PositionManager

manager = PositionManager()

# Process fill
from src.trading.models import Fill

fill = Fill(
    order_id="ORD001",
    symbol=symbol,
    side=OrderSide.BUY,
    quantity=Decimal("100"),
    fill_price=Decimal("150.00"),
    fill_time=datetime.now()
)

manager.process_fill(fill)

# Get position
position = manager.get_position(symbol)
print(position.quantity)  # 100
print(position.unrealized_pnl)  # Current P&L

# Update price
manager.update_price(symbol, Decimal("155.00"), datetime.now())

# Get summary
summary = manager.get_position_summary()
print(summary['unrealized_pnl'])
```

#### ExecutionEngine

Execute orders through broker adapters.

```python
from src.trading.execution_engine import ExecutionEngine
from src.adapters.simulated_broker import SimulatedBroker

# Create components
order_manager = OrderManager()
position_manager = PositionManager()
portfolio = Portfolio(initial_cash=Decimal("100000"))
event_bus = EventBus()

# Create engine
engine = ExecutionEngine(
    order_manager=order_manager,
    position_manager=position_manager,
    portfolio=portfolio,
    event_bus=event_bus
)

# Set broker
broker = SimulatedBroker()
engine.set_broker_adapter(broker)

# Start engine
await engine.start()

# Submit order
order = Order(symbol=symbol, side=OrderSide.BUY, quantity=Decimal("100"))
await engine.submit_order(order)

# Stop engine
await engine.stop()
```

---

### Portfolio

#### Portfolio

Manage portfolio cash and positions.

```python
from src.portfolio.portfolio import Portfolio
from decimal import Decimal

# Create portfolio with $100k initial cash
portfolio = Portfolio(initial_cash=Decimal("100000.00"))

# Get cash
print(portfolio.cash)  # 100000.00

# Get total value
print(portfolio.total_value)  # cash + positions_value

# Get positions
positions = portfolio.get_all_positions()
for position in positions:
    print(f"{position.symbol}: {position.quantity}")

# Take snapshot
snapshot = portfolio.take_snapshot()
print(snapshot.total_value)

# Get summary
summary = portfolio.get_summary()
print(summary['total_return'])
```

#### Performance Metrics

Calculate performance statistics.

```python
from src.portfolio.metrics import PerformanceCalculator

# Get snapshots from portfolio
snapshots = portfolio.get_snapshots()

# Calculate metrics
metrics = PerformanceCalculator.calculate_metrics(snapshots)

print(f"Sharpe Ratio: {metrics.sharpe_ratio}")
print(f"Max Drawdown: {metrics.max_drawdown}%")
print(f"Annualized Return: {metrics.annualized_return}%")
print(f"Volatility: {metrics.volatility}%")

# Calculate VaR
returns = PerformanceCalculator.calculate_returns(equity_curve)
var = PerformanceCalculator.calculate_var(returns, confidence_level=0.95)
print(f"VaR (95%): {var}")
```

---

### Risk Management

#### RiskManager

Enforce risk rules and position sizing.

```python
from src.risk.risk_manager import RiskManager

# Create risk manager
risk_manager = RiskManager(portfolio)

# Configure limits
risk_manager.max_position_size_percent = 10.0  # 10% per position
risk_manager.max_drawdown_percent = 20.0  # Stop at 20% DD
risk_manager._max_concentration_percent = 25.0  # Max 25% per symbol

# Check order
order = Order(symbol=symbol, side=OrderSide.BUY, quantity=Decimal("100"))
current_price = Decimal("150.00")

passed, reason = risk_manager.check_order(order, current_price)
if passed:
    print("Order approved")
else:
    print(f"Order rejected: {reason}")

# Calculate position size
shares = risk_manager.calculate_position_size(
    symbol=symbol,
    price=Decimal("150.00"),
    risk_per_trade_percent=1.0,  # Risk 1% per trade
    stop_loss_percent=2.0  # 2% stop loss
)
print(f"Recommended position size: {shares}")

# Get risk summary
summary = risk_manager.get_risk_summary()
print(f"Current drawdown: {summary['current_drawdown']}%")
print(f"Trading halted: {summary['trading_halted']}")
```

---

### Algorithms

#### Strategy Base Class

Create custom strategies by extending `Strategy`.

```python
from src.algorithms.strategy import Strategy, StrategyConfig
from src.data.models import Bar, Tick
from src.trading.models import Fill

class MyStrategy(Strategy):
    def __init__(self, config, portfolio, event_bus):
        super().__init__(config, portfolio, event_bus)
        self.fast_sma = SMA(period=10)
        self.slow_sma = SMA(period=30)
    
    def on_bar(self, bar: Bar) -> None:
        """Called on each new bar"""
        # Update indicators
        fast_val = self.fast_sma.update(bar.close)
        slow_val = self.slow_sma.update(bar.close)
        
        if not (self.fast_sma.is_ready and self.slow_sma.is_ready):
            return
        
        # Trading logic
        position = self.get_position(bar.symbol)
        
        if fast_val > slow_val and position == 0:
            # Buy signal
            quantity = self._calculate_position_size(bar.close)
            self.buy_market(bar.symbol, quantity)
        
        elif fast_val < slow_val and position > 0:
            # Sell signal
            self.sell_market(bar.symbol, position)
    
    def on_tick(self, tick: Tick) -> None:
        """Called on each tick (optional)"""
        pass
    
    def on_fill(self, fill: Fill) -> None:
        """Called on order fill (optional)"""
        print(f"Fill received: {fill.fill_id}")
    
    def _calculate_position_size(self, price) -> Decimal:
        """Calculate position size"""
        portfolio_value = self._portfolio.total_value
        position_value = portfolio_value * Decimal("0.1")  # 10% of portfolio
        return Decimal(int(position_value / price))
```

#### Indicators

Built-in technical indicators.

```python
from src.algorithms.indicators import SMA, EMA, RSI, MACD, BollingerBands

# SMA
sma = SMA(period=20)
for price in prices:
    value = sma.update(Decimal(str(price)))
print(f"SMA: {sma.value}")

# EMA
ema = EMA(period=12)
ema.update(Decimal("100.00"))

# RSI
rsi = RSI(period=14)
for price in prices:
    rsi.update(Decimal(str(price)))
print(f"RSI: {rsi.value}")  # 0-100

# MACD
macd = MACD(fast_period=12, slow_period=26, signal_period=9)
macd.update(Decimal("100.00"))
print(f"MACD Line: {macd.macd_line}")
print(f"Signal Line: {macd.signal_line}")
print(f"Histogram: {macd.histogram}")

# Bollinger Bands
bb = BollingerBands(period=20, num_std=2.0)
bb.update(Decimal("100.00"))
print(f"Upper: {bb.upper}")
print(f"Middle: {bb.middle}")
print(f"Lower: {bb.lower}")
print(f"%B: {bb.percent_b(Decimal('105.00'))}")

# Indicator Manager
from src.algorithms.indicators import IndicatorManager

manager = IndicatorManager()
manager.add("SMA20", SMA(20))
manager.add("RSI14", RSI(14))

results = manager.update_all(Decimal("100.00"))
values = manager.get_all_values()
```

#### Sample Strategies

Pre-built strategies.

```python
from src.algorithms.sample_strategies import (
    SMAStrategy,
    RSIStrategy,
    MACDStrategy,
    BollingerBandsStrategy
)

# SMA Crossover
sma_config = StrategyConfig(
    name="SMA_Cross",
    symbols=[symbol],
    parameters={
        "fast_period": 10,
        "slow_period": 30,
        "position_size": 0.1  # 10% of portfolio
    }
)

# RSI Mean Reversion
rsi_config = StrategyConfig(
    name="RSI_MeanReversion",
    symbols=[symbol],
    parameters={
        "rsi_period": 14,
        "oversold": 30,
        "overbought": 70
    }
)

# MACD Trend Following
macd_config = StrategyConfig(
    name="MACD_Trend",
    symbols=[symbol],
    parameters={
        "fast_period": 12,
        "slow_period": 26,
        "signal_period": 9
    }
)
```

#### Strategy Manager

Manage multiple strategies.

```python
from src.algorithms.strategy_manager import StrategyManager

manager = StrategyManager(portfolio, event_bus)

# Register strategy classes
manager.register_strategy_class("SMA", SMAStrategy)
manager.register_strategy_class("RSI", RSIStrategy)

# Create strategies
sma_strategy = manager.create_strategy("SMA", sma_config)
rsi_strategy = manager.create_strategy("RSI", rsi_config)

# Control strategies
manager.start_all()
manager.pause_strategy(sma_strategy.strategy_id)
manager.resume_strategy(sma_strategy.strategy_id)
manager.stop_all()

# Get summary
summary = manager.get_summary()
print(f"Total strategies: {summary['total_strategies']}")
print(f"Running: {summary['running_strategies']}")
```

---

### Backtesting

#### BacktestEngine

Run strategy backtests.

```python
from src.backtesting.engine import BacktestEngine, BacktestConfig
from datetime import datetime
from decimal import Decimal

# Configure backtest
config = BacktestConfig(
    start_date=datetime(2023, 1, 1),
    end_date=datetime(2023, 12, 31),
    symbols=[Symbol(ticker="AAPL"), Symbol(ticker="MSFT")],
    resolution=Resolution.DAILY,
    initial_cash=Decimal("100000.00"),
    commission_per_share=Decimal("0.005"),
    slippage_percent=0.001
)

# Create engine
engine = BacktestEngine(config)

# Load data
engine.load_historical_data(Symbol(ticker="AAPL"), aapl_bars)
engine.load_historical_data(Symbol(ticker="MSFT"), msft_bars)

# Register strategy
engine.register_strategy("SMA", SMAStrategy)
engine.add_strategy("SMA", {"fast_period": 10, "slow_period": 30})

# Run
import asyncio
results = asyncio.run(engine.run())

# View results
results.print_report()

# Get detailed results
summary = results.get_summary()
equity_curve = results.get_equity_curve()
monthly_returns = results.get_monthly_returns()

# Save to dict
data = results.to_dict()
```

#### Parameter Optimization

Optimize strategy parameters.

```python
from src.backtesting.optimization import ParameterOptimizer

# Define parameter grid
parameter_grid = {
    "fast_period": [5, 10, 15, 20],
    "slow_period": [30, 50, 100],
    "position_size": [0.05, 0.1, 0.2]
}

# Create optimizer
optimizer = ParameterOptimizer(
    strategy_class=SMAStrategy,
    config=config,
    parameter_grid=parameter_grid
)

# Set scoring function (default: Sharpe ratio)
optimizer.set_scoring_function(lambda r: r.sharpe_ratio)

# Run optimization
best_result = asyncio.run(optimizer.optimize(data))

print(f"Best parameters: {best_result.parameters}")
print(f"Best score: {best_result.score}")

# Get top results
top_10 = optimizer.get_top_results(10)

# Analyze parameter sensitivity
sensitivity = optimizer.analyze_parameter_sensitivity("fast_period")
for param_value, metrics in sensitivity.items():
    print(f"{param_value}: avg_sharpe={metrics['avg_sharpe']:.2f}")

# Save results
optimizer.save_results("optimization_results.json")

# Get as DataFrame
df = optimizer.get_results_dataframe()
```

---

## Examples

### Complete Backtest Example

```python
import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from src.backtesting.engine import BacktestEngine, BacktestConfig
from src.algorithms.sample_strategies import SMAStrategy
from src.data.models import Symbol, Bar, Resolution

async def run_backtest():
    # Configuration
    config = BacktestConfig(
        start_date=datetime(2023, 1, 1),
        end_date=datetime(2023, 6, 30),
        symbols=[Symbol(ticker="AAPL")],
        initial_cash=Decimal("100000.00")
    )
    
    # Create engine
    engine = BacktestEngine(config)
    
    # Generate sample data (replace with real data)
    symbol = Symbol(ticker="AAPL")
    bars = []
    base_price = 150.0
    for i in range(180):
        timestamp = datetime(2023, 1, 1) + timedelta(days=i)
        price = base_price + (i * 0.1)  # Upward trend
        bar = Bar(
            symbol=symbol,
            timestamp=timestamp,
            open=Decimal(str(price - 1)),
            high=Decimal(str(price + 2)),
            low=Decimal(str(price - 2)),
            close=Decimal(str(price)),
            volume=1000000
        )
        bars.append(bar)
    
    # Load data
    engine.load_historical_data(symbol, bars)
    
    # Register and add strategy
    engine.register_strategy("SMA", SMAStrategy)
    engine.add_strategy("SMA", {
        "fast_period": 10,
        "slow_period": 30,
        "position_size": 0.1
    })
    
    # Run
    results = await engine.run()
    
    # Print report
    results.print_report()
    
    return results

# Run
if __name__ == "__main__":
    results = asyncio.run(run_backtest())
```

### Live Data Example

```python
from src.adapters.yahoo_finance import YahooFinanceAdapter
from src.data.models import Symbol

# Create adapter
adapter = YahooFinanceAdapter()

# Get historical data
symbol = Symbol(ticker="AAPL")
bars = await adapter.get_history(
    symbol=symbol,
    start_date=datetime(2023, 1, 1),
    end_date=datetime(2023, 12, 31),
    resolution=Resolution.DAILY
)

print(f"Loaded {len(bars)} bars")
```

### Custom Strategy Example

```python
from src.algorithms.strategy import Strategy, StrategyConfig
from src.algorithms.indicators import RSI, BollingerBands
from src.data.models import Bar

class MyCustomStrategy(Strategy):
    """RSI + Bollinger Bands Strategy"""
    
    def __init__(self, config, portfolio, event_bus):
        super().__init__(config, portfolio, event_bus)
        
        # Get parameters
        rsi_period = config.get("rsi_period", 14)
        bb_period = config.get("bb_period", 20)
        
        # Initialize indicators
        self.rsi = RSI(period=rsi_period)
        self.bb = BollingerBands(period=bb_period)
    
    def on_bar(self, bar: Bar) -> None:
        # Update indicators
        rsi_val = self.rsi.update(bar.close)
        self.bb.update(bar.close)
        
        if not (self.rsi.is_ready and self.bb.is_ready):
            return
        
        # Get current position
        position = self.get_position(bar.symbol)
        
        # Entry: RSI oversold + price near lower band
        percent_b = self.bb.percent_b(bar.close)
        if rsi_val and percent_b:
            if rsi_val < 30 and percent_b < 0.2 and position == 0:
                # Buy signal
                quantity = self._calculate_size(bar.close)
                self.buy_market(bar.symbol, quantity)
        
        # Exit: RSI overbought OR price near upper band
        if rsi_val and percent_b:
            if (rsi_val > 70 or percent_b > 0.8) and position > 0:
                # Sell signal
                self.sell_market(bar.symbol, position)
    
    def _calculate_size(self, price: Decimal) -> Decimal:
        """Calculate position size"""
        portfolio_value = self._portfolio.total_value
        position_pct = self.param("position_size", 0.1)
        position_value = portfolio_value * Decimal(str(position_pct))
        return Decimal(int(position_value / price))

# Use the strategy
config = StrategyConfig(
    name="RSI_BB_Strategy",
    symbols=[Symbol(ticker="AAPL")],
    parameters={
        "rsi_period": 14,
        "bb_period": 20,
        "position_size": 0.1
    }
)
```

---

## Event System

### EventBus

```python
from src.engine.events import EventBus, EventType

event_bus = EventBus()

# Subscribe to events
event_bus.subscribe(EventType.BAR, lambda bar: print(f"Bar: {bar}"))
event_bus.subscribe(EventType.ORDER, lambda order: print(f"Order: {order}"))
event_bus.subscribe(EventType.FILL, lambda fill: print(f"Fill: {fill}"))

# Emit events
event_bus.emit(EventType.BAR, bar_data)
event_bus.emit(EventType.ORDER, order_data)

# Unsubscribe
event_bus.unsubscribe(EventType.BAR, callback)
```

### Event Types

- `EventType.BAR` - New bar data
- `EventType.TICK` - New tick data
- `EventType.ORDER` - Order submitted
- `EventType.FILL` - Order filled
- `EventType.POSITION` - Position update
- `EventType.ERROR` - Error occurred

---

## Configuration

### Environment Variables

```bash
ALGO_LOG_LEVEL=INFO
ALGO_LOG_FILE=logs/algo.log
ALGO_DB_PATH=data/algo.db
```

### YAML Config

```yaml
# config/default.yaml
logging:
  level: INFO
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: logs/algo.log
  max_size: 10485760
  backup_count: 5

data:
  cache_dir: ./cache
  storage_dir: ./data
```

---

## License

MIT License - See LICENSE file for details.

---

## Support

For issues and feature requests, please open an issue on the project repository.
