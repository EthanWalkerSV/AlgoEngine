"""Tests for time keeper"""

import pytest
from datetime import datetime, timedelta
from src.engine.timekeeper import TimeKeeper


class TestTimeKeeper:
    """Test time keeper functionality"""
    
    def test_backtest_mode(self):
        """Test backtest mode time setting"""
        tk = TimeKeeper(is_backtest=True)
        
        test_time = datetime(2023, 1, 1, 12, 0, 0)
        tk.set_time(test_time)
        
        assert tk.current_time.year == 2023
        assert tk.current_time.month == 1
        assert tk.current_time.day == 1
    
    def test_backtest_advance(self):
        """Test advancing time in backtest mode"""
        tk = TimeKeeper(is_backtest=True)
        
        start = datetime(2023, 1, 1)
        tk.set_time(start)
        tk.advance_time(timedelta(hours=1))
        
        assert tk.current_time.hour == 1
    
    def test_live_mode_cannot_set_time(self):
        """Test that time cannot be set in live mode"""
        tk = TimeKeeper(is_backtest=False)
        
        with pytest.raises(RuntimeError):
            tk.set_time(datetime(2023, 1, 1))
    
    def test_market_hours_check(self):
        """Test market hours checking"""
        tk = TimeKeeper(is_backtest=True, timezone_str="US/Eastern")
        
        # Monday at 10:00 AM
        monday_morning = datetime(2023, 6, 12, 10, 0, 0)
        tk.set_time(monday_morning)
        
        assert tk.is_market_open(market_timezone="US/Eastern")
        
        # Saturday
        saturday = datetime(2023, 6, 10, 12, 0, 0)
        tk.set_time(saturday)
        
        assert not tk.is_market_open(market_timezone="US/Eastern")
    
    def test_schedule_task(self):
        """Test scheduling a task"""
        tk = TimeKeeper(is_backtest=True)
        
        executed = []
        
        def task():
            executed.append(True)
        
        run_at = datetime(2023, 1, 1, 12, 0, 0)
        tk.schedule("test_task", task, run_at)
        
        # Set time after scheduled time
        tk.set_time(datetime(2023, 1, 1, 13, 0, 0))
        
        # In a real scenario, the task would be executed by run()
        # Here we just verify the schedule was created
        assert "test_task" in tk._schedules
    
    def test_unschedule_task(self):
        """Test unscheduling a task"""
        tk = TimeKeeper(is_backtest=True)
        
        def task():
            pass
        
        tk.schedule("test_task", task, datetime.now())
        tk.unschedule("test_task")
        
        assert "test_task" not in tk._schedules
    
    def test_timezone_conversion(self):
        """Test timezone conversion"""
        tk = TimeKeeper(timezone_str="UTC")
        
        utc_time = datetime(2023, 1, 1, 12, 0, 0)
        est_time = tk.to_timezone(utc_time, "US/Eastern")
        
        # EST is 5 hours behind UTC
        assert est_time.hour == 7
