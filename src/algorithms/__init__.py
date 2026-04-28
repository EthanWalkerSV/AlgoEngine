"""Algorithmic trading strategies for AlgoEngine"""

from .strategy import Strategy, StrategyConfig, StrategyState
from .strategy_manager import StrategyManager
from .indicators import (
    Indicator, SMA, EMA, RSI, MACD, BollingerBands, ATR, IndicatorManager
)
from .sample_strategies import (
    SMAStrategy,
    RSIStrategy,
    MACDStrategy,
    BollingerBandsStrategy,
)

__all__ = [
    # Strategy base
    "Strategy",
    "StrategyConfig",
    "StrategyState",
    "StrategyManager",
    # Indicators
    "Indicator",
    "SMA",
    "EMA",
    "RSI",
    "MACD",
    "BollingerBands",
    "ATR",
    "IndicatorManager",
    # Sample strategies
    "SMAStrategy",
    "RSIStrategy",
    "MACDStrategy",
    "BollingerBandsStrategy",
]
