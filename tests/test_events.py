"""Tests for event system"""

import pytest
import asyncio
from datetime import datetime
from src.engine.events import Event, EventType, EventBus


class TestEvent:
    """Test event data structure"""
    
    def test_event_creation(self):
        """Test creating an event"""
        event = Event(
            event_type=EventType.TICK,
            timestamp=datetime.now(),
            data={"price": 100.0},
            symbol="AAPL"
        )
        assert event.event_type == EventType.TICK
        assert event.symbol == "AAPL"
        assert event.data["price"] == 100.0


class TestEventBus:
    """Test event bus functionality"""
    
    def test_subscribe_and_emit(self):
        """Test subscribing and emitting events"""
        bus = EventBus()
        received = []
        
        def handler(event):
            received.append(event)
        
        bus.subscribe(EventType.TICK, handler)
        
        event = Event(
            event_type=EventType.TICK,
            timestamp=datetime.now()
        )
        bus.emit(event)
        
        assert len(received) == 1
        assert received[0].event_type == EventType.TICK
    
    def test_unsubscribe(self):
        """Test unsubscribing from events"""
        bus = EventBus()
        received = []
        
        def handler(event):
            received.append(event)
        
        bus.subscribe(EventType.TICK, handler)
        bus.unsubscribe(EventType.TICK, handler)
        
        event = Event(
            event_type=EventType.TICK,
            timestamp=datetime.now()
        )
        bus.emit(event)
        
        assert len(received) == 0
    
    def test_global_handler(self):
        """Test global event handler"""
        bus = EventBus()
        received = []
        
        def handler(event):
            received.append(event)
        
        bus.subscribe_all(handler)
        
        event = Event(
            event_type=EventType.TICK,
            timestamp=datetime.now()
        )
        bus.emit(event)
        
        assert len(received) == 1
    
    def test_handler_count(self):
        """Test getting handler count"""
        bus = EventBus()
        
        def handler1(event):
            pass
        
        def handler2(event):
            pass
        
        bus.subscribe(EventType.TICK, handler1)
        bus.subscribe(EventType.TICK, handler2)
        
        assert bus.get_handler_count(EventType.TICK) == 2
        assert bus.get_handler_count() == 2
    
    def test_clear_handlers(self):
        """Test clearing handlers"""
        bus = EventBus()
        
        def handler(event):
            pass
        
        bus.subscribe(EventType.TICK, handler)
        bus.clear_handlers(EventType.TICK)
        
        assert bus.get_handler_count(EventType.TICK) == 0
    
    @pytest.mark.asyncio
    async def test_async_handler(self):
        """Test async event handler"""
        bus = EventBus()
        received = []
        
        async def handler(event):
            received.append(event)
        
        bus.subscribe(EventType.TICK, handler, async_handler=True)
        
        event = Event(
            event_type=EventType.TICK,
            timestamp=datetime.now()
        )
        bus.emit(event)
        
        # Give async handler time to execute
        await asyncio.sleep(0.1)
        
        assert len(received) == 1
