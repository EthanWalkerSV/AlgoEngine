"""Data processing modules for AlgoEngine"""

from .models import (
    DataType,
    Resolution,
    Symbol,
    BaseData,
    Tick,
    Bar,
    Quote,
    Trade,
    OrderBook,
    OrderBookLevel,
    FundamentalData,
    News,
    MarketData,
)
from .feed import DataFeed, StreamingDataFeed, DataCache, DataAggregator

# Optional import for storage (requires pyarrow)
try:
    from .storage import DataStorage
except ImportError:
    DataStorage = None  # type: ignore

__all__ = [
    # Models
    "DataType",
    "Resolution",
    "Symbol",
    "BaseData",
    "Tick",
    "Bar",
    "Quote",
    "Trade",
    "OrderBook",
    "OrderBookLevel",
    "FundamentalData",
    "News",
    "MarketData",
    # Feed
    "DataFeed",
    "StreamingDataFeed",
    "DataCache",
    "DataAggregator",
    # Storage (optional)
    "DataStorage",
]
