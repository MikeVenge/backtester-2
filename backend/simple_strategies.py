"""
Simple pre-defined strategies for testing
"""
from datetime import datetime
import pandas as pd
from typing import Dict


class RotationStrategy:
    """Buy every N days and hold for M days"""
    
    def __init__(self, buy_every_n_days: int, hold_for_days: int):
        self.buy_every_n_days = buy_every_n_days
        self.hold_for_days = hold_for_days
        self.last_entry_date = None
        self.days_since_last_entry = 0
    
    def entry_signal(self, market_data: pd.DataFrame, ticker: str, timestamp: datetime) -> bool:
        """
        Generate entry signal: Buy every N days
        """
        # On first day, buy
        if self.last_entry_date is None:
            self.last_entry_date = timestamp
            self.days_since_last_entry = 0
            return True
        
        # Calculate days since last entry
        days_diff = (timestamp - self.last_entry_date).days
        
        # If it's been N days or more, buy again
        if days_diff >= self.buy_every_n_days:
            self.last_entry_date = timestamp
            self.days_since_last_entry = 0
            return True
        
        return False
    
    def exit_signal(
        self, 
        market_data: pd.DataFrame, 
        ticker: str, 
        timestamp: datetime, 
        position
    ) -> bool:
        """
        Exit signal is handled by time-based exit in the strategy engine
        This returns False as we rely on timeBasedExit parameter
        """
        return False


def create_rotation_strategy_functions(buy_every_n_days: int, hold_for_days: int):
    """
    Create entry and exit signal functions for rotation strategy
    
    Args:
        buy_every_n_days: Number of days between purchases
        hold_for_days: Number of days to hold each position
    
    Returns:
        Tuple of (entry_func, exit_func)
    """
    strategy = RotationStrategy(buy_every_n_days, hold_for_days)
    
    def entry_func(market_data, ticker, timestamp):
        return strategy.entry_signal(market_data, ticker, timestamp)
    
    def exit_func(market_data, ticker, timestamp, position):
        return strategy.exit_signal(market_data, ticker, timestamp, position)
    
    return entry_func, exit_func

