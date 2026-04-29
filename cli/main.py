"""Main CLI entry point for AlgoEngine"""

import asyncio
import click
from pathlib import Path
from datetime import datetime
from decimal import Decimal
from typing import List, Type

from src.utils.logger import setup_logging, get_logger
from src.utils.config import Config, get_config
from src.data.models import Symbol, Resolution
from src.backtesting.engine import BacktestEngine, BacktestConfig
from src.backtesting.results import BacktestResults
from src.algorithms.strategy import Strategy
from src.adapters.yahoo_finance import YahooFinanceAdapter


logger = get_logger("cli")


@click.group()
@click.option('--config', '-c', type=click.Path(), help='Configuration file path')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.pass_context
def cli(ctx, config, verbose):
    """AlgoEngine CLI"""
    ctx.ensure_object(dict)
    
    # Load configuration
    if config:
        ctx.obj['config'] = Config.load(config)
    else:
        ctx.obj['config'] = get_config()
    
    # Setup logging
    log_level = "DEBUG" if verbose else ctx.obj['config'].logging.level
    setup_logging(
        log_dir=ctx.obj['config'].logging.dir,
        log_level=log_level,
        console_output=True,
        file_output=True
    )


def _load_strategy_class(algorithm_path: str) -> Type[Strategy]:
    """Load strategy class from file path"""
    import importlib.util
    import sys
    
    path = Path(algorithm_path)
    if not path.exists():
        raise click.BadParameter(f"Algorithm file not found: {algorithm_path}")
    
    module_name = path.stem
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise click.BadParameter(f"Cannot load algorithm file: {algorithm_path}")
    
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    
    # Find Strategy subclass
    for name in dir(module):
        obj = getattr(module, name)
        if (isinstance(obj, type) and 
            issubclass(obj, Strategy) and 
            obj is not Strategy):
            return obj
    
    raise click.BadParameter(f"No Strategy subclass found in {algorithm_path}")


def _parse_symbols(symbols_str: str) -> List[Symbol]:
    """Parse comma-separated symbols"""
    return [Symbol(ticker=s.strip().upper()) for s in symbols_str.split(',')]


@cli.command()
@click.option('--algorithm', '-a', required=True, help='Algorithm file path')
@click.option('--start-date', '-s', required=True, help='Start date (YYYY-MM-DD)')
@click.option('--end-date', '-e', required=True, help='End date (YYYY-MM-DD)')
@click.option('--symbols', '-sym', required=True, help='Comma-separated list of symbols')
@click.option('--cash', default=100000, help='Initial cash amount')
@click.option('--resolution', '-r', default='DAILY', 
              type=click.Choice(['TICK', 'SECOND', 'MINUTE', 'HOUR', 'DAILY', 'WEEKLY', 'MONTHLY']),
              help='Data resolution')
@click.pass_context
def backtest(ctx, algorithm, start_date, end_date, symbols, cash, resolution):
    """Run algorithm backtest"""
    config = ctx.obj['config']
    logger.info("Starting backtest...")
    logger.info(f"Algorithm: {algorithm}")
    logger.info(f"Symbols: {symbols}")
    
    # Parse dates
    try:
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
    except ValueError:
        raise click.BadParameter("Dates must be in YYYY-MM-DD format")
    
    if start >= end:
        raise click.BadParameter("start-date must be before end-date")
    
    # Parse symbols
    symbol_list = _parse_symbols(symbols)
    
    # Load strategy class
    try:
        strategy_class = _load_strategy_class(algorithm)
        logger.info(f"Loaded strategy: {strategy_class.__name__}")
    except Exception as e:
        logger.error(f"Failed to load strategy: {e}")
        raise click.ClickException(str(e))
    
    # Run backtest
    async def run_backtest():
        # Initialize data adapter
        data_adapter = YahooFinanceAdapter(cache_data=True)
        await data_adapter.connect()
        
        # Download historical data
        click.echo(f"Downloading historical data for {len(symbol_list)} symbols...")
        historical_data = {}
        
        for symbol in symbol_list:
            bars = await data_adapter.download_and_cache(symbol, start, end, Resolution[resolution])
            if bars:
                historical_data[symbol] = bars
                click.echo(f"  {symbol.ticker}: {len(bars)} bars")
            else:
                click.echo(f"  {symbol.ticker}: No data available")
        
        await data_adapter.disconnect()
        
        if not historical_data:
            raise click.ClickException("No historical data available for any symbol")
        
        # Setup backtest engine
        backtest_config = BacktestConfig(
            start_date=start,
            end_date=end,
            symbols=symbol_list,
            resolution=Resolution[resolution],
            initial_cash=Decimal(str(cash))
        )
        
        engine = BacktestEngine(backtest_config)
        
        # Load data into engine
        for symbol, bars in historical_data.items():
            engine.load_historical_data(symbol, bars)
        
        # Register and add strategy
        engine.register_strategy(strategy_class.__name__, strategy_class)
        strategy = engine.add_strategy(strategy_class.__name__)
        
        if not strategy:
            raise click.ClickException("Failed to create strategy instance")
        
        # Run backtest
        click.echo("\nRunning backtest...")
        results = await engine.run()
        
        # Display results
        _display_backtest_results(results)
        
        return results
    
    try:
        asyncio.run(run_backtest())
    except Exception as e:
        logger.error(f"Backtest failed: {e}")
        raise click.ClickException(str(e))


def _display_backtest_results(results: BacktestResults) -> None:
    """Display backtest results in formatted output"""
    click.echo("\n" + "=" * 50)
    click.echo("BACKTEST RESULTS")
    click.echo("=" * 50)
    
    # Basic metrics
    click.echo(f"\nPeriod: {results.start_date.date()} to {results.end_date.date()}")
    click.echo(f"Initial Cash: ${float(results.initial_cash):,.2f}")
    click.echo(f"Final Value: ${float(results.final_value):,.2f}")
    
    # Returns
    total_return = float(results.total_return)
    click.echo(f"\nTotal Return: {total_return:+.2f}%")
    
    if results.annualized_return is not None:
        click.echo(f"Annualized Return: {float(results.annualized_return):.2f}%")
    
    # Risk metrics
    if results.volatility is not None:
        click.echo(f"Volatility: {float(results.volatility):.2f}%")
    
    if results.sharpe_ratio is not None:
        click.echo(f"Sharpe Ratio: {float(results.sharpe_ratio):.2f}")
    
    if results.max_drawdown is not None:
        click.echo(f"Max Drawdown: {float(results.max_drawdown):.2f}%")
    
    # Trade statistics
    click.echo(f"\nTotal Trades: {results.total_trades}")
    click.echo(f"Win Rate: {results.win_rate:.1f}%")
    
    click.echo("=" * 50)


@cli.command()
@click.option('--algorithm', '-a', required=True, help='Algorithm file path')
@click.option('--broker', '-b', default='paper', 
              type=click.Choice(['paper', 'simulated']),
              help='Broker adapter (paper=simulated, simulated=legacy)')
@click.option('--symbols', '-sym', required=True, help='Comma-separated list of symbols')
@click.option('--cash', default=100000, help='Initial cash amount for paper trading')
@click.pass_context
def live(ctx, algorithm, broker, symbols, cash):
    """Run live/paper trading"""
    config = ctx.obj['config']
    logger.info("Starting live trading...")
    logger.info(f"Algorithm: {algorithm}")
    logger.info(f"Broker: {broker}")
    logger.info(f"Symbols: {symbols}")
    
    # Parse symbols
    symbol_list = _parse_symbols(symbols)
    
    # Load strategy class
    try:
        strategy_class = _load_strategy_class(algorithm)
        logger.info(f"Loaded strategy: {strategy_class.__name__}")
    except Exception as e:
        logger.error(f"Failed to load strategy: {e}")
        raise click.ClickException(str(e))
    
    # Run live trading
    async def run_live():
        from src.engine.events import EventBus
        from src.portfolio.portfolio import Portfolio
        from src.algorithms.strategy_manager import StrategyManager
        from src.trading.execution_engine import ExecutionEngine
        from src.trading.order_manager import OrderManager
        from src.trading.position_manager import PositionManager
        from src.adapters.simulated_broker import SimulatedBroker
        
        # Initialize components
        event_bus = EventBus()
        portfolio = Portfolio(initial_cash=Decimal(str(cash)))
        
        order_manager = OrderManager()
        position_manager = PositionManager()
        
        # Use simulated broker for paper trading
        broker_adapter = SimulatedBroker(fill_probability=1.0, latency_ms=100)
        await broker_adapter.connect()
        
        execution_engine = ExecutionEngine(
            order_manager=order_manager,
            position_manager=position_manager,
            portfolio=portfolio,
            event_bus=event_bus
        )
        execution_engine.set_broker_adapter(broker_adapter)
        
        # Initialize strategy manager
        strategy_manager = StrategyManager(
            portfolio=portfolio,
            event_bus=event_bus
        )
        
        # Register and create strategy
        strategy_manager.register_strategy_class(strategy_class.__name__, strategy_class)
        strategy_config = type('Config', (), {
            'name': strategy_class.__name__,
            'symbols': symbol_list,
            'parameters': {}
        })()
        strategy = strategy_manager.create_strategy(strategy_class.__name__, strategy_config)
        
        if not strategy:
            raise click.ClickException("Failed to create strategy instance")
        
        # Start components
        await execution_engine.start()
        strategy_manager.start_all()
        
        click.echo(f"\n{'='*50}")
        click.echo(f"PAPER TRADING STARTED")
        click.echo(f"{'='*50}")
        click.echo(f"Strategy: {strategy_class.__name__}")
        click.echo(f"Symbols: {[s.ticker for s in symbol_list]}")
        click.echo(f"Initial Cash: ${cash:,.2f}")
        click.echo(f"\nPress Ctrl+C to stop...")
        click.echo(f"{'='*50}\n")
        
        try:
            # Simulate market data feed
            data_adapter = YahooFinanceAdapter(cache_data=True)
            await data_adapter.connect()
            
            # Get latest prices and emit as ticks
            while True:
                for symbol in symbol_list:
                    try:
                        # Get recent daily data as simulation
                        from datetime import timedelta
                        end = datetime.now()
                        start = end - timedelta(days=5)
                        bars = data_adapter.get_bars(symbol, start, end, Resolution.DAILY)
                        
                        if bars:
                            latest_bar = bars[-1]
                            # Create tick from bar close
                            from src.data.models import Tick
                            tick = Tick(
                                symbol=symbol,
                                timestamp=datetime.now(),
                                bid_price=latest_bar.close * Decimal("0.999"),
                                ask_price=latest_bar.close * Decimal("1.001"),
                                bid_size=Decimal("100"),
                                ask_size=Decimal("100")
                            )
                            event_bus.emit(type('Event', (), {
                                'event_type': 'TICK',
                                'symbol': symbol.ticker,
                                'data': tick,
                                'timestamp': datetime.now()
                            })())
                    except Exception as e:
                        logger.warning(f"Error fetching data for {symbol.ticker}: {e}")
                
                await asyncio.sleep(5)  # Update every 5 seconds
                
                # Display portfolio status
                click.echo(f"Portfolio Value: ${float(portfolio.total_value):,.2f} | "
                          f"Cash: ${float(portfolio.cash):,.2f} | "
                          f"Positions: {len(portfolio.positions)}")
                
        except KeyboardInterrupt:
            click.echo("\n\nStopping trading...")
        finally:
            strategy_manager.stop_all()
            await execution_engine.stop()
            await broker_adapter.disconnect()
            await data_adapter.disconnect()
            
            # Final summary
            click.echo(f"\n{'='*50}")
            click.echo("FINAL PNL SUMMARY")
            click.echo(f"{'='*50}")
            click.echo(f"Initial Cash: ${float(Decimal(str(cash))):,.2f}")
            click.echo(f"Final Value: ${float(portfolio.total_value):,.2f}")
            pnl = float(portfolio.total_value - Decimal(str(cash)))
            click.echo(f"P&L: ${pnl:+,.2f} ({pnl/float(cash)*100:+.2f}%)")
            click.echo(f"{'='*50}")
    
    try:
        asyncio.run(run_live())
    except click.ClickException:
        raise
    except Exception as e:
        logger.error(f"Live trading failed: {e}")
        raise click.ClickException(str(e))


@cli.command()
@click.option('--data-dir', '-d', default='data', help='Data directory')
@click.option('--source', '-s', default='yahoo', 
              type=click.Choice(['yahoo']),
              help='Data source')
@click.option('--start-date', '-s', required=True, help='Start date (YYYY-MM-DD)')
@click.option('--end-date', '-e', required=True, help='End date (YYYY-MM-DD)')
@click.option('--resolution', '-r', default='DAILY',
              type=click.Choice(['TICK', 'SECOND', 'MINUTE', 'HOUR', 'DAILY', 'WEEKLY', 'MONTHLY']),
              help='Data resolution')
@click.argument('symbols', nargs=-1, required=True)
@click.pass_context
def download(ctx, data_dir, source, start_date, end_date, resolution, symbols):
    """Download historical data"""
    logger.info(f"Downloading data from {source}...")
    logger.info(f"Symbols: {symbols}")
    logger.info(f"Date range: {start_date} to {end_date}")
    
    if not symbols:
        raise click.BadParameter("At least one symbol is required")
    
    # Parse dates
    try:
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
    except ValueError:
        raise click.BadParameter("Dates must be in YYYY-MM-DD format")
    
    if start >= end:
        raise click.BadParameter("start-date must be before end-date")
    
    # Create data directory
    data_path = Path(data_dir)
    data_path.mkdir(parents=True, exist_ok=True)
    
    # Parse symbols
    symbol_list = [Symbol(ticker=s.upper()) for s in symbols]
    
    async def download_data():
        adapter = YahooFinanceAdapter(cache_data=True)
        await adapter.connect()
        
        success_count = 0
        fail_count = 0
        
        click.echo(f"\nDownloading {len(symbol_list)} symbols...")
        click.echo(f"Resolution: {resolution}")
        click.echo(f"Date range: {start.date()} to {end.date()}")
        click.echo("-" * 50)
        
        for symbol in symbol_list:
            try:
                bars = await adapter.download_and_cache(
                    symbol, start, end, Resolution[resolution]
                )
                
                if bars:
                    click.echo(f"{symbol.ticker:6} - {len(bars):5} bars - OK")
                    success_count += 1
                else:
                    click.echo(f"{symbol.ticker:6} - No data available")
                    fail_count += 1
                    
            except Exception as e:
                logger.error(f"Failed to download {symbol.ticker}: {e}")
                click.echo(f"{symbol.ticker:6} - ERROR: {e}")
                fail_count += 1
        
        await adapter.disconnect()
        
        click.echo("-" * 50)
        click.echo(f"Download complete: {success_count} success, {fail_count} failed")
        click.echo(f"Data cached in: {data_path.absolute()}")
    
    try:
        asyncio.run(download_data())
    except Exception as e:
        logger.error(f"Download failed: {e}")
        raise click.ClickException(str(e))


@cli.command()
def config():
    """Show current configuration"""
    cfg = get_config()
    click.echo(f"Environment: {cfg.env}")
    click.echo(f"Debug: {cfg.debug}")
    click.echo(f"Timezone: {cfg.timezone}")
    click.echo(f"Data directory: {cfg.data.data_dir}")
    click.echo(f"Log level: {cfg.logging.level}")


@cli.command()
def version():
    """Show version information"""
    from src import __version__
    click.echo(f"AlgoEngine v{__version__}")


def main():
    """Entry point"""
    cli()


if __name__ == '__main__':
    main()
