"""Main CLI entry point for AlgoEngine"""

import asyncio
import click
from pathlib import Path

from src.utils.logger import setup_logging, get_logger
from src.utils.config import Config, get_config


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


@cli.command()
@click.option('--algorithm', '-a', required=True, help='Algorithm file path')
@click.option('--start-date', '-s', help='Start date (YYYY-MM-DD)')
@click.option('--end-date', '-e', help='End date (YYYY-MM-DD)')
@click.option('--symbols', '-sym', help='Comma-separated list of symbols')
@click.option('--cash', default=100000, help='Initial cash amount')
@click.pass_context
def backtest(ctx, algorithm, start_date, end_date, symbols, cash):
    """Run algorithm backtest"""
    config = ctx.obj['config']
    logger.info("Starting backtest...")
    logger.info(f"Algorithm: {algorithm}")
    logger.info(f"Symbols: {symbols}")
    
    # TODO: Implement backtest execution
    click.echo("Backtest mode - implementation pending")


@cli.command()
@click.option('--algorithm', '-a', required=True, help='Algorithm file path')
@click.option('--broker', '-b', default='paper', help='Broker adapter')
@click.option('--symbols', '-sym', help='Comma-separated list of symbols')
@click.pass_context
def live(ctx, algorithm, broker, symbols):
    """Run live trading"""
    config = ctx.obj['config']
    logger.info("Starting live trading...")
    logger.info(f"Algorithm: {algorithm}")
    logger.info(f"Broker: {broker}")
    
    # TODO: Implement live trading
    click.echo("Live trading mode - implementation pending")


@cli.command()
@click.option('--data-dir', '-d', default='data', help='Data directory')
@click.option('--source', '-s', default='yahoo', help='Data source')
@click.argument('symbols', nargs=-1)
@click.pass_context
def download(ctx, data_dir, source, symbols):
    """Download historical data"""
    logger.info(f"Downloading data from {source}...")
    logger.info(f"Symbols: {symbols}")
    
    # TODO: Implement data download
    click.echo("Data download - implementation pending")


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
