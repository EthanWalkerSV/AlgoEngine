"""Trading models for AlgoEngine"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum, auto
from typing import Optional, Dict, Any
import itertools

from ..data.models import Symbol

# Global counter for unique order IDs
_order_counter = itertools.count(1)


class OrderType(Enum):
    """Order types"""
    MARKET = auto()
    LIMIT = auto()
    STOP = auto()
    STOP_LIMIT = auto()


class OrderSide(Enum):
    """Order side (buy or sell)"""
    BUY = auto()
    SELL = auto()


class OrderStatus(Enum):
    """Order lifecycle status"""
    SUBMITTED = auto()      # Order submitted to broker
    ACCEPTED = auto()       # Order accepted by broker
    PENDING = auto()        # Order waiting for trigger (stop/limit)
    PARTIALLY_FILLED = auto()
    FILLED = auto()
    CANCELLED = auto()
    REJECTED = auto()
    EXPIRED = auto()


class TimeInForce(Enum):
    """Order time in force"""
    DAY = auto()            # Valid for trading day
    GTC = auto()            # Good till cancelled
    IOC = auto()            # Immediate or cancel
    FOK = auto()            # Fill or kill


@dataclass
class Order:
    """Order representation"""
    symbol: Symbol
    side: OrderSide
    quantity: Decimal
    order_type: OrderType = OrderType.MARKET
    
    # Price information (optional for market orders)
    limit_price: Optional[Decimal] = None
    stop_price: Optional[Decimal] = None
    
    # Order configuration
    time_in_force: TimeInForce = TimeInForce.DAY
    
    # Order identification
    order_id: str = field(default_factory=lambda: f"ORD_{next(_order_counter)}_{datetime.now().strftime('%H%M%S')}")
    client_order_id: Optional[str] = None
    broker_order_id: Optional[str] = None
    
    # Status tracking
    status: OrderStatus = OrderStatus.SUBMITTED
    filled_quantity: Decimal = field(default_factory=lambda: Decimal("0"))
    remaining_quantity: Optional[Decimal] = None
    avg_fill_price: Optional[Decimal] = None
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    submitted_at: Optional[datetime] = None
    filled_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    
    # Additional properties
    tags: Dict[str, Any] = field(default_factory=dict)
    strategy_id: Optional[str] = None
    
    def __post_init__(self):
        if self.remaining_quantity is None:
            self.remaining_quantity = self.quantity
    
    @property
    def is_active(self) -> bool:
        """Check if order is still active"""
        return self.status in [
            OrderStatus.SUBMITTED,
            OrderStatus.ACCEPTED,
            OrderStatus.PENDING,
            OrderStatus.PARTIALLY_FILLED
        ]
    
    @property
    def is_filled(self) -> bool:
        """Check if order is completely filled"""
        return self.status == OrderStatus.FILLED
    
    @property
    def is_cancelled(self) -> bool:
        """Check if order is cancelled"""
        return self.status == OrderStatus.CANCELLED
    
    def update_fill(self, fill_quantity: Decimal, fill_price: Decimal) -> None:
        """Update order with fill information"""
        if self.filled_quantity == Decimal("0"):
            self.avg_fill_price = fill_price
        else:
            # Calculate weighted average
            total_value = (self.filled_quantity * self.avg_fill_price) + (fill_quantity * fill_price)
            total_quantity = self.filled_quantity + fill_quantity
            self.avg_fill_price = total_value / total_quantity
        
        self.filled_quantity += fill_quantity
        self.remaining_quantity -= fill_quantity
        self.updated_at = datetime.now()
        
        if self.remaining_quantity <= 0:
            self.status = OrderStatus.FILLED
            self.filled_at = datetime.now()
        else:
            self.status = OrderStatus.PARTIALLY_FILLED
    
    def cancel(self) -> None:
        """Mark order as cancelled"""
        if self.is_active:
            self.status = OrderStatus.CANCELLED
            self.cancelled_at = datetime.now()
            self.updated_at = datetime.now()


@dataclass
class Fill:
    """Trade fill information"""
    order_id: str
    symbol: Symbol
    side: OrderSide
    quantity: Decimal
    fill_price: Decimal
    fill_time: datetime
    
    fill_id: str = field(default_factory=lambda: f"FILL_{next(_order_counter)}_{datetime.now().strftime('%H%M%S')}")
    commission: Decimal = field(default_factory=lambda: Decimal("0"))
    slippage: Decimal = field(default_factory=lambda: Decimal("0"))
    
    @property
    def value(self) -> Decimal:
        """Total value of fill"""
        return self.quantity * self.fill_price


@dataclass
class Position:
    """Position in a security"""
    symbol: Symbol
    side: OrderSide  # LONG or SHORT (BUY/SELL)
    
    quantity: Decimal = field(default_factory=lambda: Decimal("0"))
    avg_entry_price: Optional[Decimal] = None
    
    # Current market data
    current_price: Optional[Decimal] = None
    last_update_time: Optional[datetime] = None
    
    # Tracking
    opened_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Statistics
    total_trades: int = 0
    realized_pnl: Decimal = field(default_factory=lambda: Decimal("0"))
    
    @property
    def is_long(self) -> bool:
        """Check if position is long"""
        return self.side == OrderSide.BUY and self.quantity > 0
    
    @property
    def is_short(self) -> bool:
        """Check if position is short"""
        return self.side == OrderSide.SELL and self.quantity > 0
    
    @property
    def market_value(self) -> Decimal:
        """Current market value of position"""
        if self.current_price is None:
            return Decimal("0")
        return self.quantity * self.current_price
    
    @property
    def unrealized_pnl(self) -> Decimal:
        """Unrealized profit/loss"""
        if self.avg_entry_price is None or self.current_price is None:
            return Decimal("0")
        
        if self.is_long:
            return self.quantity * (self.current_price - self.avg_entry_price)
        else:
            return self.quantity * (self.avg_entry_price - self.current_price)
    
    @property
    def unrealized_pnl_percent(self) -> float:
        """Unrealized P&L as percentage"""
        if self.avg_entry_price is None or self.avg_entry_price == 0:
            return 0.0
        return float(self.unrealized_pnl / (self.quantity * self.avg_entry_price)) * 100
    
    def add_fill(self, fill: Fill) -> None:
        """Add a fill to position"""
        if self.avg_entry_price is None:
            self.avg_entry_price = fill.fill_price
            self.opened_at = fill.fill_time
        else:
            # Calculate new average entry price
            total_value = (self.quantity * self.avg_entry_price) + (fill.quantity * fill.fill_price)
            total_quantity = self.quantity + fill.quantity
            self.avg_entry_price = total_value / total_quantity
        
        self.quantity += fill.quantity
        self.total_trades += 1
        self.updated_at = fill.fill_time
    
    def reduce(self, quantity: Decimal, price: Decimal, time: datetime) -> Decimal:
        """Reduce position and return realized P&L"""
        if quantity >= self.quantity:
            quantity = self.quantity
        
        # Calculate realized P&L
        if self.avg_entry_price:
            if self.is_long:
                pnl = quantity * (price - self.avg_entry_price)
            else:
                pnl = quantity * (self.avg_entry_price - price)
            self.realized_pnl += pnl
        
        self.quantity -= quantity
        self.total_trades += 1
        self.updated_at = time
        
        return self.realized_pnl
    
    def update_price(self, price: Decimal, time: datetime) -> None:
        """Update current market price"""
        self.current_price = price
        self.last_update_time = time


@dataclass
class Trade:
    """Completed trade record"""
    trade_id: str
    symbol: Symbol
    entry_time: datetime
    exit_time: datetime
    side: OrderSide
    quantity: Decimal
    entry_price: Decimal
    exit_price: Decimal
    
    # P&L
    realized_pnl: Decimal
    commission: Decimal = field(default_factory=lambda: Decimal("0"))
    slippage: Decimal = field(default_factory=lambda: Decimal("0"))
    
    # Reference
    entry_order_id: Optional[str] = None
    exit_order_id: Optional[str] = None
    strategy_id: Optional[str] = None
    
    @property
    def gross_pnl(self) -> Decimal:
        """Gross P&L before costs"""
        return self.realized_pnl + self.commission + self.slippage
    
    @property
    def net_pnl(self) -> Decimal:
        """Net P&L after costs"""
        return self.realized_pnl - self.commission - self.slippage
    
    @property
    def return_percent(self) -> float:
        """Return as percentage of invested capital"""
        invested = float(self.quantity * self.entry_price)
        if invested == 0:
            return 0.0
        return float(self.net_pnl) / invested * 100
    
    @property
    def duration(self) -> float:
        """Trade duration in seconds"""
        return (self.exit_time - self.entry_time).total_seconds()


@dataclass
class CommissionModel:
    """Commission calculation model"""
    per_share: Decimal = field(default_factory=lambda: Decimal("0"))  # Per share fee
    min_per_order: Decimal = field(default_factory=lambda: Decimal("0"))  # Minimum per order
    max_percent: Decimal = field(default_factory=lambda: Decimal("1"))  # Maximum % of trade value
    flat_fee: Decimal = field(default_factory=lambda: Decimal("0"))  # Flat fee per order
    
    def calculate(self, quantity: Decimal, price: Decimal) -> Decimal:
        """Calculate commission for a trade"""
        trade_value = quantity * price
        
        # Per share commission
        commission = quantity * self.per_share
        
        # Add flat fee
        commission += self.flat_fee
        
        # Apply minimum
        commission = max(commission, self.min_per_order)
        
        # Apply maximum percentage cap
        max_commission = trade_value * self.max_percent / 100
        commission = min(commission, max_commission)
        
        return commission


@dataclass
class SlippageModel:
    """Slippage calculation model"""
    fixed_slippage: Decimal = field(default_factory=lambda: Decimal("0"))  # Fixed dollar amount
    percentage: Decimal = field(default_factory=lambda: Decimal("0"))  # Percentage of price
    volume_impact: Decimal = field(default_factory=lambda: Decimal("0"))  # Per unit volume impact
    
    def calculate(self, price: Decimal, quantity: Decimal, volume: Decimal = Decimal("0")) -> Decimal:
        """Calculate slippage"""
        slippage = self.fixed_slippage
        slippage += price * self.percentage / 100
        
        if volume > 0:
            slippage += (quantity / volume) * self.volume_impact
        
        return slippage
