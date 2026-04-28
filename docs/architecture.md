# AlgoEngine Architecture

## Overview

AlgoEngine is a modular, event-driven algorithmic trading platform designed for multi-asset CFD trading.

## Core Components

### 1. Engine (`src/engine/`)

The central orchestrator that coordinates all components:

- **Engine**: Main class managing algorithm lifecycle
- **EventBus**: Central event distribution system
- **TimeKeeper**: Time management for backtesting and live trading
- **Interfaces**: Abstract base classes for all components

### 2. Utilities (`src/utils/`)

Supporting infrastructure:

- **Logger**: Centralized logging with file rotation
- **Config**: Configuration management with YAML and env support

### 3. Data (`src/data/`)

Data processing and management (Phase 2)

### 4. Trading (`src/trading/`)

Trade execution and order management (Phase 3)

### 5. Portfolio (`src/portfolio/`)

Portfolio and position management (Phase 5)

### 6. Risk (`src/risk/`)

Risk management and monitoring (Phase 5)

### 7. Algorithms (`src/algorithms/`)

Algorithm framework and base classes (Phase 4)

### 8. Adapters (`src/adapters/`)

Broker and data source adapters (Phase 3)

## Event Flow

```
DataFeed -> EventBus -> Algorithm
                           |
                           v
                    TradingLogic
                           |
                           v
            TransactionHandler -> Broker
                           |
                           v
                    PortfolioManager
                           |
                           v
                    RiskManager
```

## Key Interfaces

### IAlgorithm
Base interface for all trading algorithms. Implementations must provide:
- `initialize()`: Setup logic
- `on_data()`: Handle market data
- `on_order_event()`: Handle order updates
- `terminate()`: Cleanup logic

### IDataFeed
Interface for market data providers:
- `connect()`: Establish connection
- `subscribe()`: Subscribe to symbols
- `get_history()`: Retrieve historical data

### ITransactionHandler
Interface for order execution:
- `process_order()`: Submit orders
- `cancel_order()`: Cancel orders
- `get_open_orders()`: Query orders

### IPortfolio
Interface for portfolio management:
- `get_cash()`: Available cash
- `get_positions()`: Current positions
- `process_fill()`: Update on fills

## Configuration

Configuration is managed through YAML files and environment variables:

```yaml
env: development
timezone: UTC

database:
  host: localhost
  port: 5432

logging:
  level: INFO
  dir: logs
```

Environment variables override config values:
- `ALGO_ENV`: Environment name
- `ALGO_DB_HOST`: Database host
- `ALGO_LOG_LEVEL`: Log level

## Testing

Run tests with pytest:
```bash
pytest tests/ -v
```

## Next Steps

1. **Phase 2**: Implement data feed adapters and historical data storage
2. **Phase 3**: Build order management and brokerage adapters
3. **Phase 4**: Create algorithm base classes and technical indicators
4. **Phase 5**: Implement portfolio and risk management
5. **Phase 6-8**: Tools, testing, and documentation
