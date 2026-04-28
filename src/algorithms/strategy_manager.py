"""Strategy manager for AlgoEngine"""

from typing import Dict, List, Optional, Type, Any

from .strategy import Strategy, StrategyConfig
from ..portfolio.portfolio import Portfolio
from ..engine.events import EventBus
from ..utils.logger import get_logger

logger = get_logger("algorithms.manager")


class StrategyManager:
    """Manage multiple trading strategies"""
    
    def __init__(self, portfolio: Portfolio, event_bus: EventBus) -> None:
        self._portfolio = portfolio
        self._event_bus = event_bus
        self._strategies: Dict[str, Strategy] = {}
        self._strategy_configs: Dict[str, StrategyConfig] = {}
        self._strategy_classes: Dict[str, Type[Strategy]] = {}
        
        logger.info("StrategyManager initialized")
    
    def register_strategy_class(
        self,
        name: str,
        strategy_class: Type[Strategy]
    ) -> None:
        """Register a strategy class by name"""
        self._strategy_classes[name] = strategy_class
        logger.info(f"Registered strategy class: {name}")
    
    def create_strategy(
        self,
        name: str,
        config: StrategyConfig
    ) -> Optional[Strategy]:
        """Create a strategy instance from registered class"""
        if name not in self._strategy_classes:
            logger.error(f"Strategy class not found: {name}")
            return None
        
        strategy_class = self._strategy_classes[name]
        strategy = strategy_class(config, self._portfolio, self._event_bus)
        
        self._strategies[strategy.strategy_id] = strategy
        self._strategy_configs[strategy.strategy_id] = config
        
        logger.info(f"Created strategy {strategy.strategy_id} from class {name}")
        return strategy
    
    def add_strategy(self, strategy: Strategy) -> None:
        """Add an existing strategy instance"""
        self._strategies[strategy.strategy_id] = strategy
        logger.info(f"Added strategy {strategy.strategy_id}")
    
    def remove_strategy(self, strategy_id: str) -> bool:
        """Remove a strategy"""
        if strategy_id not in self._strategies:
            return False
        
        strategy = self._strategies[strategy_id]
        strategy.stop()
        
        del self._strategies[strategy_id]
        del self._strategy_configs[strategy_id]
        
        logger.info(f"Removed strategy {strategy_id}")
        return True
    
    def get_strategy(self, strategy_id: str) -> Optional[Strategy]:
        """Get strategy by ID"""
        return self._strategies.get(strategy_id)
    
    def get_all_strategies(self) -> List[Strategy]:
        """Get all strategies"""
        return list(self._strategies.values())
    
    def get_running_strategies(self) -> List[Strategy]:
        """Get all running strategies"""
        return [s for s in self._strategies.values() if s.is_running]
    
    def start_strategy(self, strategy_id: str) -> bool:
        """Start a specific strategy"""
        strategy = self._strategies.get(strategy_id)
        if not strategy:
            return False
        
        strategy.start()
        return True
    
    def start_all(self) -> int:
        """Start all strategies"""
        count = 0
        for strategy in self._strategies.values():
            if not strategy.is_running:
                strategy.start()
                count += 1
        
        logger.info(f"Started {count} strategies")
        return count
    
    def stop_strategy(self, strategy_id: str) -> bool:
        """Stop a specific strategy"""
        strategy = self._strategies.get(strategy_id)
        if not strategy:
            return False
        
        strategy.stop()
        return True
    
    def stop_all(self) -> int:
        """Stop all strategies"""
        count = 0
        for strategy in self._strategies.values():
            strategy.stop()
            count += 1
        
        logger.info(f"Stopped {count} strategies")
        return count
    
    def pause_strategy(self, strategy_id: str) -> bool:
        """Pause a specific strategy"""
        strategy = self._strategies.get(strategy_id)
        if not strategy:
            return False
        
        strategy.pause()
        return True
    
    def resume_strategy(self, strategy_id: str) -> bool:
        """Resume a specific strategy"""
        strategy = self._strategies.get(strategy_id)
        if not strategy:
            return False
        
        strategy.resume()
        return True
    
    def pause_all(self) -> int:
        """Pause all running strategies"""
        count = 0
        for strategy in self._strategies.values():
            if strategy.is_running:
                strategy.pause()
                count += 1
        
        logger.info(f"Paused {count} strategies")
        return count
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all strategies"""
        return {
            'total_strategies': len(self._strategies),
            'running_strategies': len(self.get_running_strategies()),
            'registered_classes': list(self._strategy_classes.keys()),
            'strategies': {
                sid: s.get_summary() for sid, s in self._strategies.items()
            }
        }
