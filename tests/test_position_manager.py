"""Tests for position manager"""

import pytest
from decimal import Decimal
from datetime import datetime

from src.trading.position_manager import PositionManager
from src.trading.models import OrderSide, Fill
from src.data.models import Symbol


class TestPositionManager:
    """Test PositionManager class"""
    
    @pytest.fixture
    def manager(self):
        """Create position manager instance"""
        return PositionManager()
    
    @pytest.fixture
    def sample_fill(self):
        """Create sample fill"""
        return Fill(
            order_id="ORD001",
            symbol=Symbol(ticker="AAPL"),
            side=OrderSide.BUY,
            quantity=Decimal("100"),
            fill_price=Decimal("150.00"),
            fill_time=datetime.now()
        )
    
    def test_process_fill_creates_position(self, manager, sample_fill):
        """Test that fill creates new position"""
        manager.process_fill(sample_fill)
        
        position = manager.get_position(sample_fill.symbol)
        assert position is not None
        assert position.quantity == Decimal("100")
        assert position.is_long
    
    def test_process_fill_updates_position(self, manager, sample_fill):
        """Test that additional fills update position"""
        manager.process_fill(sample_fill)
        
        # Second fill
        fill2 = Fill(
            order_id="ORD002",
            symbol=Symbol(ticker="AAPL"),
            side=OrderSide.BUY,
            quantity=Decimal("50"),
            fill_price=Decimal("155.00"),
            fill_time=datetime.now()
        )
        manager.process_fill(fill2)
        
        position = manager.get_position(sample_fill.symbol)
        assert position.quantity == Decimal("150")
    
    def test_process_fill_closes_position(self, manager, sample_fill):
        """Test that opposite fill closes position"""
        # First create long position
        manager.process_fill(sample_fill)
        
        # Then sell to close
        sell_fill = Fill(
            order_id="ORD003",
            symbol=Symbol(ticker="AAPL"),
            side=OrderSide.SELL,  # Opposite side
            quantity=Decimal("100"),
            fill_price=Decimal("160.00"),
            fill_time=datetime.now()
        )
        trade = manager.process_fill(sell_fill)
        
        position = manager.get_position(sample_fill.symbol)
        assert position is None or position.quantity == 0
        assert trade is not None
        assert trade.realized_pnl == Decimal("1000.00")  # 100 * (160 - 150)
    
    def test_get_unrealized_pnl(self, manager, sample_fill):
        """Test unrealized P&L calculation"""
        manager.process_fill(sample_fill)
        
        # Update price
        manager.update_price(sample_fill.symbol, Decimal("160.00"), datetime.now())
        
        unrealized = manager.get_unrealized_pnl()
        assert unrealized == Decimal("1000.00")  # 100 * (160 - 150)
    
    def test_get_all_positions(self, manager):
        """Test getting all positions"""
        # Create positions for different symbols
        for ticker in ["AAPL", "MSFT", "GOOGL"]:
            fill = Fill(
                order_id=f"ORD_{ticker}",
                symbol=Symbol(ticker=ticker),
                side=OrderSide.BUY,
                quantity=Decimal("100"),
                fill_price=Decimal("100.00"),
                fill_time=datetime.now()
            )
            manager.process_fill(fill)
        
        positions = manager.get_all_positions()
        assert len(positions) == 3
    
    def test_position_summary(self, manager, sample_fill):
        """Test position summary"""
        manager.process_fill(sample_fill)
        manager.update_price(sample_fill.symbol, Decimal("160.00"), datetime.now())
        
        summary = manager.get_position_summary()
        
        assert summary['total_positions'] == 1
        assert summary['long_positions'] == 1
        assert summary['unrealized_pnl'] == 1000.0
