"""Tests for performance metrics"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta

from src.portfolio.metrics import PerformanceMetrics, PerformanceCalculator
from src.portfolio.portfolio import PortfolioSnapshot


class TestPerformanceCalculator:
    """Test PerformanceCalculator"""
    
    @pytest.fixture
    def sample_snapshots(self):
        """Create sample portfolio snapshots"""
        base_time = datetime.now()
        snapshots = []
        
        # Create 10 days of equity curve
        values = [100000, 101000, 102000, 101500, 103000,  
                  102000, 104000, 103500, 105000, 106000]
        
        for i, value in enumerate(values):
            snapshots.append(PortfolioSnapshot(
                timestamp=base_time + timedelta(days=i),
                cash=Decimal(str(value * 0.1)),
                positions_value=Decimal(str(value * 0.9)),
                total_value=Decimal(str(value)),
                unrealized_pnl=Decimal("0"),
                realized_pnl=Decimal("0")
            ))
        
        return snapshots
    
    def test_calculate_returns(self):
        """Test return calculation"""
        equity_curve = [100, 110, 105, 115]
        returns = PerformanceCalculator.calculate_returns(equity_curve)
        
        assert len(returns) == 3
        assert returns[0] == pytest.approx(0.10, abs=0.01)  # 10% gain
        assert returns[1] == pytest.approx(-0.045, abs=0.01)  # ~-4.5% loss
        assert returns[2] == pytest.approx(0.095, abs=0.01)  # ~9.5% gain
    
    def test_calculate_sharpe_ratio(self):
        """Test Sharpe ratio calculation"""
        returns = [0.01, 0.02, -0.01, 0.015, 0.005]
        sharpe = PerformanceCalculator.calculate_sharpe_ratio(returns)
        
        # Sharpe should be positive for positive returns
        assert sharpe > 0
    
    def test_calculate_max_drawdown(self):
        """Test max drawdown calculation"""
        equity_curve = [100, 110, 105, 115, 100, 120, 90, 130]
        
        max_dd, duration = PerformanceCalculator.calculate_max_drawdown(equity_curve)
        
        # Max drawdown is from 120 to 90 = 25%
        assert max_dd > 0
        assert duration > 0
    
    def test_calculate_metrics(self, sample_snapshots):
        """Test comprehensive metrics calculation"""
        metrics = PerformanceCalculator.calculate_metrics(sample_snapshots)
        
        assert metrics is not None
        assert metrics.total_return > 0  # 6% gain (100k to 106k)
        assert metrics.volatility >= 0
        assert metrics.sharpe_ratio is not None
        assert metrics.max_drawdown >= 0
    
    def test_calculate_var(self):
        """Test Value at Risk calculation"""
        returns = [0.05, -0.02, 0.03, -0.05, 0.01, -0.03, 0.02]
        var = PerformanceCalculator.calculate_var(returns, confidence_level=0.95)
        
        # VaR should be negative (potential loss)
        assert var < 0
    
    def test_empty_returns(self):
        """Test handling of empty returns"""
        sharpe = PerformanceCalculator.calculate_sharpe_ratio([])
        assert sharpe == 0.0
        
        returns = PerformanceCalculator.calculate_returns([100])
        assert returns == []
    
    def test_single_snapshot(self):
        """Test metrics with single snapshot"""
        snapshots = [PortfolioSnapshot(
            timestamp=datetime.now(),
            cash=Decimal("100000"),
            positions_value=Decimal("0"),
            total_value=Decimal("100000"),
            unrealized_pnl=Decimal("0"),
            realized_pnl=Decimal("0")
        )]
        
        metrics = PerformanceCalculator.calculate_metrics(snapshots)
        assert metrics is None  # Not enough data


class TestPerformanceMetrics:
    """Test PerformanceMetrics dataclass"""
    
    def test_metrics_creation(self):
        """Test creating performance metrics"""
        metrics = PerformanceMetrics(
            total_return=10.5,
            annualized_return=25.0,
            volatility=15.0,
            sharpe_ratio=1.5,
            max_drawdown=5.0,
            max_drawdown_duration=10,
            win_rate=0.6,
            profit_factor=2.0,
            avg_trade_return=1.5,
            calmar_ratio=5.0
        )
        
        assert metrics.total_return == 10.5
        assert metrics.sharpe_ratio == 1.5
        assert metrics.calmar_ratio == 5.0
