"""Simple Moving Average Crossover Strategy Example"""

from decimal import Decimal
from typing import List, Dict, Any
from collections import deque

from src.engine.interfaces import (
    IAlgorithm, Symbol, Order, OrderType, OrderEvent,
    Position, Bar, Tick
)


class SimpleMovingAverageCrossover(IAlgorithm):
    """
    Simple Moving Average Crossover Strategy
    
    Buys when short SMA crosses above long SMA
    Sells when short SMA crosses below long SMA
    """
    
    def __init__(
        self,
        short_window: int = 20,
        long_window: int = 50,
        symbol: str = "AAPL"
    ):
        self.short_window = short_window
        self.long_window = long_window
        self.symbol = Symbol(ticker=symbol, security_type="EQUITY")
        
        self.short_prices: deque = deque(maxlen=short_window)
        self.long_prices: deque = deque(maxlen=long_window)
        
        self.invested: bool = False
        self.warming_up: bool = True
        
    def initialize(self) -> None:
        """Initialize the algorithm"""
        print(f"Initializing SMA Crossover: {self.short_window}/{self.long_window}")
    
    def on_data(self, data: Any) -> None:
        """Process new market data"""
        if isinstance(data, Bar):
            if data.symbol.ticker != self.symbol.ticker:
                return
            
            price = float(data.close)
            self.short_prices.append(price)
            self.long_prices.append(price)
            
            if self.warming_up:
                return
            
            if len(self.long_prices) < self.long_window:
                return
            
            short_sma = sum(self.short_prices) / len(self.short_prices)
            long_sma = sum(self.long_prices) / len(self.long_prices)
            
            # Trading logic
            if short_sma > long_sma and not self.invested:
                self._enter_long()
            elif short_sma < long_sma and self.invested:
                self._exit_position()
    
    def _enter_long(self) -> None:
        """Enter long position"""
        print(f"Signal: BUY {self.symbol.ticker}")
        self.invested = True
    
    def _exit_position(self) -> None:
        """Exit position"""
        print(f"Signal: SELL {self.symbol.ticker}")
        self.invested = False
    
    def on_order_event(self, event: OrderEvent) -> None:
        """Handle order events"""
        print(f"Order {event.order_id}: {event.status.name}")
    
    def on_position_changed(self, position: Position) -> None:
        """Handle position changes"""
        print(f"Position update: {position.symbol.ticker} {position.side.name}")
    
    def on_warmup_finished(self) -> None:
        """Called when warmup is complete"""
        self.warming_up = False
        print("Warmup finished - starting live trading")
    
    def on_end_of_day(self) -> None:
        """Called at end of day"""
        print("End of day - generating report")
    
    def terminate(self, message: str = "") -> None:
        """Terminate the algorithm"""
        print(f"Algorithm terminated: {message}")
    
    @property
    def is_warming_up(self) -> bool:
        """Check if in warmup"""
        return self.warming_up


if __name__ == "__main__":
    # Example usage
    algo = SimpleMovingAverageCrossover(
        short_window=10,
        long_window=30,
        symbol="AAPL"
    )
    algo.initialize()
    print("Algorithm created successfully")
