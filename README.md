# AlgoEngine

An open-source algorithmic trading platform supporting multi-asset CFD trading including forex, indices, stocks, crypto, and commodities.

## Features

- **Multi-Asset Support**: Trade forex, indices, stocks, crypto, and commodities via CFDs
- **Backtesting Engine**: Historical data backtesting with performance optimization
- **Live Trading**: Real-time trading with multiple brokerage adapters
- **Risk Management**: Comprehensive risk controls and monitoring
- **Event-Driven Architecture**: Asynchronous, event-based processing
- **Modular Design**: Plugin system for custom strategies and indicators

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest

# Start the engine
python -m cli.main
```

## Project Structure

```
algoengine/
├── src/
│   ├── engine/        # Core engine
│   ├── data/          # Data processing
│   ├── trading/       # Trade execution
│   ├── portfolio/     # Portfolio management
│   ├── risk/          # Risk management
│   ├── algorithms/    # Algorithm framework
│   ├── adapters/      # Adapters
│   └── utils/         # Utilities
├── tests/             # Tests
├── docs/              # Documentation
├── examples/          # Examples
├── cli/               # CLI tools
└── config/            # Configuration
```

## License

MIT License - see LICENSE file for details.
