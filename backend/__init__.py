"""
Backtester Backend Package
A comprehensive backtesting engine for trading strategies
"""

__version__ = "1.0.0"
__author__ = "Backtester Team"

from .backtest_engine import BacktestEngine
from .portfolio import Portfolio, Position, Trade
from .strategy import StrategyEngine
from .data_fetcher import DataFetcher
from .performance import PerformanceAnalyzer

__all__ = [
    'BacktestEngine',
    'Portfolio',
    'Position',
    'Trade',
    'StrategyEngine',
    'DataFetcher',
    'PerformanceAnalyzer'
]

