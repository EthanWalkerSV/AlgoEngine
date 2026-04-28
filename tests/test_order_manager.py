"""Tests for order manager"""

import pytest
from decimal import Decimal
from datetime import datetime

from src.trading.order_manager import OrderManager
from src.trading.models import Order, OrderSide, OrderType, Fill
from src.data.models import Symbol


class TestOrderManager:
    """Test OrderManager class"""
    
    @pytest.fixture
    def manager(self):
        """Create order manager instance"""
        return OrderManager()
    
    @pytest.fixture
    def sample_order(self):
        """Create sample order"""
        return Order(
            symbol=Symbol(ticker="AAPL"),
            side=OrderSide.BUY,
            quantity=Decimal("100"),
            order_type=OrderType.MARKET
        )
    
    def test_register_order(self, manager, sample_order):
        """Test registering an order"""
        manager.register_order(sample_order)
        
        retrieved = manager.get_order(sample_order.order_id)
        assert retrieved == sample_order
    
    def test_get_active_orders(self, manager, sample_order):
        """Test getting active orders"""
        manager.register_order(sample_order)
        
        active = manager.get_active_orders()
        assert len(active) == 1
        assert active[0] == sample_order
    
    def test_process_fill(self, manager, sample_order):
        """Test processing a fill"""
        manager.register_order(sample_order)
        
        fill = Fill(
            order_id=sample_order.order_id,
            symbol=sample_order.symbol,
            side=sample_order.side,
            quantity=Decimal("100"),
            fill_price=Decimal("150.00"),
            fill_time=datetime.now()
        )
        
        manager.process_fill(sample_order.order_id, fill)
        
        assert sample_order.filled_quantity == Decimal("100")
        assert sample_order.is_filled
    
    def test_cancel_order(self, manager, sample_order):
        """Test cancelling an order"""
        manager.register_order(sample_order)
        
        result = manager.cancel_order(sample_order.order_id)
        
        assert result is True
        assert sample_order.is_cancelled
    
    def test_cancel_all_orders(self, manager):
        """Test cancelling all orders"""
        for i in range(3):
            order = Order(
                symbol=Symbol(ticker="AAPL"),
                side=OrderSide.BUY,
                quantity=Decimal("100")
            )
            manager.register_order(order)
        
        cancelled = manager.cancel_all_orders()
        
        assert cancelled == 3
    
    def test_order_callback(self, manager, sample_order):
        """Test order callback registration"""
        callback_called = []
        
        def on_order(order):
            callback_called.append(order.order_id)
        
        manager.on_order(on_order)
        manager.register_order(sample_order)
        
        assert len(callback_called) == 1
        assert callback_called[0] == sample_order.order_id
    
    def test_fill_callback(self, manager, sample_order):
        """Test fill callback registration"""
        callback_called = []
        
        def on_fill(fill):
            callback_called.append(fill.order_id)
        
        manager.on_fill(on_fill)
        manager.register_order(sample_order)
        
        fill = Fill(
            order_id=sample_order.order_id,
            symbol=sample_order.symbol,
            side=sample_order.side,
            quantity=Decimal("100"),
            fill_price=Decimal("150.00"),
            fill_time=datetime.now()
        )
        manager.process_fill(sample_order.order_id, fill)
        
        assert len(callback_called) == 1
