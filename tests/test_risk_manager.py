"""Tests for risk management"""

import pytest
from decimal import Decimal

from src.risk.risk_manager import RiskManager, RiskContext
from src.portfolio.portfolio import Portfolio
from src.trading.models import Order, OrderSide, OrderType
from src.data.models import Symbol


class TestRiskManager:
    """Test RiskManager class"""
    
    @pytest.fixture
    def portfolio(self):
        """Create portfolio with $100k"""
        return Portfolio(initial_cash=Decimal("100000.00"))
    
    @pytest.fixture
    def risk_manager(self, portfolio):
        """Create risk manager"""
        return RiskManager(portfolio)
    
    def test_position_size_limit(self, risk_manager, portfolio):
        """Test position size limit check"""
        order = Order(
            symbol=Symbol(ticker="AAPL"),
            side=OrderSide.BUY,
            quantity=Decimal("10000"),  # Way too many shares
            order_type=OrderType.MARKET
        )
        
        passed, reason = risk_manager.check_order(order, Decimal("150.00"))
        
        assert not passed
        assert "Position size" in reason
    
    def test_buying_power_check(self, risk_manager, portfolio):
        """Test insufficient buying power check"""
        # Increase limits so only buying power check fails
        risk_manager._max_position_size_percent = 200.0  # Allow large positions
        risk_manager._max_concentration_percent = 200.0  # Allow concentration
        risk_manager._max_total_exposure_percent = 200.0  # Allow exposure
        
        order = Order(
            symbol=Symbol(ticker="AAPL"),
            side=OrderSide.BUY,
            quantity=Decimal("800"),  # $120k value, exceeds $100k cash
            order_type=OrderType.MARKET
        )
        
        passed, reason = risk_manager.check_order(order, Decimal("150.00"))
        
        assert not passed
        assert "Insufficient buying power" in reason
    
    def test_valid_order_passes(self, risk_manager, portfolio):
        """Test that valid order passes risk checks"""
        order = Order(
            symbol=Symbol(ticker="AAPL"),
            side=OrderSide.BUY,
            quantity=Decimal("50"),  # $7.5k = 7.5% of portfolio, under 10% limit
            order_type=OrderType.MARKET
        )
        
        passed, reason = risk_manager.check_order(order, Decimal("150.00"))
        
        assert passed
        assert reason == "Risk check passed"
    
    def test_calculate_position_size(self, risk_manager):
        """Test position size calculation"""
        symbol = Symbol(ticker="AAPL")
        price = Decimal("150.00")
        
        shares = risk_manager.calculate_position_size(
            symbol,
            price,
            risk_per_trade_percent=1.0,
            stop_loss_percent=2.0
        )
        
        # Risk per trade = 1% of 100k = $1000
        # Risk per share = 2% of $150 = $3
        # Shares = $1000 / $3 = 333.33, rounded down to 333
        assert shares == Decimal("333")
    
    def test_drawdown_limit(self, risk_manager, portfolio):
        """Test trading halt on excessive drawdown"""
        # Simulate 30% drawdown
        portfolio.update_cash(Decimal("-30000.00"))  # Now at $70k
        
        order = Order(
            symbol=Symbol(ticker="AAPL"),
            side=OrderSide.BUY,
            quantity=Decimal("10"),
            order_type=OrderType.MARKET
        )
        
        passed, reason = risk_manager.check_order(order, Decimal("150.00"))
        
        assert not passed
        assert "drawdown" in reason.lower()
    
    def test_concentration_limit(self, risk_manager, portfolio):
        """Test concentration limit"""
        # Set concentration limit to 10% (lower than position size limit)
        risk_manager._max_concentration_percent = 10.0
        risk_manager._max_position_size_percent = 50.0  # Allow larger positions
        
        order = Order(
            symbol=Symbol(ticker="AAPL"),
            side=OrderSide.BUY,
            quantity=Decimal("100"),  # $15k = 15% of portfolio, passes 50% position limit but fails 10% concentration
            order_type=OrderType.MARKET
        )
        
        passed, reason = risk_manager.check_order(order, Decimal("150.00"))
        
        assert not passed
        assert "Concentration" in reason
    
    def test_get_risk_summary(self, risk_manager, portfolio):
        """Test risk summary generation"""
        summary = risk_manager.get_risk_summary()
        
        assert 'current_drawdown' in summary
        assert 'trading_halted' in summary
        assert 'cash_available' in summary
        assert summary['cash_available'] == 100000.0


class TestRiskContext:
    """Test RiskContext"""
    
    def test_risk_context_creation(self):
        """Test creating risk context"""
        portfolio = Portfolio()
        order = Order(
            symbol=Symbol(ticker="AAPL"),
            side=OrderSide.BUY,
            quantity=Decimal("100"),
            order_type=OrderType.MARKET
        )
        
        context = RiskContext(
            portfolio=portfolio,
            order=order,
            symbol=order.symbol,
            proposed_quantity=order.quantity,
            current_price=Decimal("150.00")
        )
        
        assert context.portfolio == portfolio
        assert context.order == order
        assert context.proposed_quantity == Decimal("100")
