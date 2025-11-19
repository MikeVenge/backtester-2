"""
Utility Functions Module
Helper functions for calculations and data processing
"""
from typing import Dict, Optional, Tuple, Any
from datetime import datetime, timedelta
import logging
import numpy as np

logger = logging.getLogger(__name__)


def calculate_commission(
    shares: float,
    price: float,
    commission_type: str,
    commission_amount: float
) -> float:
    """
    Calculate commission based on type
    
    Args:
        shares: Number of shares
        price: Price per share
        commission_type: "per-trade", "per-share", "per-contract"
        commission_amount: Commission amount
    
    Returns:
        Commission cost
    """
    if commission_type == "per-trade":
        return commission_amount
    elif commission_type == "per-share":
        return commission_amount * abs(shares)
    elif commission_type == "per-contract":
        # For options trading
        contracts = abs(shares) / 100
        return commission_amount * contracts
    else:
        logger.warning(f"Unknown commission type: {commission_type}")
        return 0.0


def calculate_total_cost(
    shares: float,
    price: float,
    commission_type: str,
    commission_amount: float,
    exchange_fees: float,
    slippage: float,
    is_buy: bool = True
) -> Tuple[float, float, float]:
    """
    Calculate total cost/proceeds for a trade including all fees
    
    Args:
        shares: Number of shares
        price: Price per share
        commission_type: Commission type
        commission_amount: Commission amount
        exchange_fees: Exchange fees as percentage
        slippage: Slippage as percentage
        is_buy: True if buying, False if selling
    
    Returns:
        (execution_price, total_cost, total_fees)
    """
    # Apply slippage (worse price for trader)
    if is_buy:
        execution_price = price * (1 + slippage / 100)
    else:
        execution_price = price * (1 - slippage / 100)
    
    # Calculate gross value
    gross_value = abs(shares) * execution_price
    
    # Calculate commission
    commission = calculate_commission(shares, execution_price, commission_type, commission_amount)
    
    # Calculate exchange fees
    exchange_fee = gross_value * (exchange_fees / 100)
    
    # Total fees
    total_fees = commission + exchange_fee
    
    # Total cost (for buys) or net proceeds (for sells)
    if is_buy:
        total_cost = gross_value + total_fees
    else:
        total_cost = gross_value - total_fees
    
    return execution_price, total_cost, total_fees


def get_execution_price(
    bar_data: Dict[str, float],
    entry_timing: str
) -> Optional[float]:
    """
    Get execution price based on entry timing setting
    
    Args:
        bar_data: Dict with OHLCV data for the bar
        entry_timing: "next-bar-open", "same-bar-close", "midpoint", "vwap"
    
    Returns:
        Execution price or None if not available
    """
    if entry_timing == "same-bar-close":
        return bar_data.get('close')
    elif entry_timing == "midpoint":
        high = bar_data.get('high')
        low = bar_data.get('low')
        if high is not None and low is not None:
            return (high + low) / 2
    elif entry_timing == "vwap":
        # VWAP calculation would require volume data
        # For simplicity, using close price as proxy
        return bar_data.get('close')
    elif entry_timing == "next-bar-open":
        # This should be handled by using next bar's open price
        # For now, return None to indicate we need to wait
        return None
    else:
        return bar_data.get('close')


def is_trading_day(timestamp: datetime, trading_days: list) -> bool:
    """
    Check if timestamp falls on an allowed trading day
    
    Args:
        timestamp: Datetime to check
        trading_days: List of allowed weekday names (e.g., ["Monday", "Tuesday"])
    
    Returns:
        True if trading is allowed on this day
    """
    if not trading_days:
        return True
    
    weekday_name = timestamp.strftime("%A")
    return weekday_name in trading_days


def calculate_atr(prices: list, period: int = 14) -> float:
    """
    Calculate Average True Range (ATR)
    
    Args:
        prices: List of (high, low, close) tuples
        period: ATR period
    
    Returns:
        ATR value
    """
    if len(prices) < period + 1:
        return 0.0
    
    true_ranges = []
    for i in range(1, len(prices)):
        high = prices[i][0]
        low = prices[i][1]
        prev_close = prices[i-1][2]
        
        tr = max(
            high - low,
            abs(high - prev_close),
            abs(low - prev_close)
        )
        true_ranges.append(tr)
    
    # Calculate average
    atr = sum(true_ranges[-period:]) / period
    return atr


def validate_backtest_config(config: dict) -> Tuple[bool, str]:
    """
    Validate backtest configuration
    
    Args:
        config: Backtest configuration dict
    
    Returns:
        (is_valid, error_message)
    """
    # Check market data
    if not config.get('marketData'):
        return False, "Market data configuration is required"
    
    market_data = config['marketData']
    
    if not market_data.get('tickers'):
        return False, "Tickers are required"
    
    if not market_data.get('startDate') or not market_data.get('endDate'):
        return False, "Start date and end date are required"
    
    # Validate date order
    start_date = market_data.get('startDate')
    end_date = market_data.get('endDate')
    
    if isinstance(start_date, str):
        start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
    if isinstance(end_date, str):
        end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
    
    if start_date >= end_date:
        return False, "Start date must be before end date"
    
    # Check portfolio settings
    if not config.get('portfolioRisk'):
        return False, "Portfolio and risk settings are required"
    
    portfolio_risk = config['portfolioRisk']
    
    if not portfolio_risk.get('initialCapital'):
        return False, "Initial capital is required"
    
    if portfolio_risk.get('initialCapital', 0) <= 0:
        return False, "Initial capital must be positive"
    
    # Check strategy settings
    if not config.get('strategy'):
        return False, "Strategy definition is required"
    
    return True, "OK"


def parse_tickers(tickers_string: str) -> list:
    """
    Parse comma-separated ticker string into list
    
    Args:
        tickers_string: Comma-separated ticker symbols
    
    Returns:
        List of ticker symbols (uppercase, stripped)
    """
    if not tickers_string:
        return []
    
    tickers = [t.strip().upper() for t in tickers_string.split(',')]
    return [t for t in tickers if t]


def format_currency(value: float) -> str:
    """Format value as currency string"""
    return f"${value:,.2f}"


def format_percent(value: float, decimals: int = 2) -> str:
    """Format value as percentage string"""
    return f"{value:.{decimals}f}%"


def get_week_start(date: datetime) -> datetime:
    """Get the start of the week (Monday) for a given date"""
    days_since_monday = date.weekday()
    week_start = date - timedelta(days=days_since_monday)
    return week_start.replace(hour=0, minute=0, second=0, microsecond=0)


def apply_borrow_cost(
    position_value: float,
    borrow_cost: float,
    days_held: int = 1
) -> float:
    """
    Calculate borrow cost for short positions
    
    Args:
        position_value: Absolute value of short position
        borrow_cost: Annual borrow cost as percentage
        days_held: Number of days
    
    Returns:
        Total borrow cost
    """
    annual_cost = abs(position_value) * (borrow_cost / 100)
    daily_cost = annual_cost / 365
    return daily_cost * days_held


def convert_numpy_types(obj: Any) -> Any:
    """
    Recursively convert numpy types to native Python types for JSON serialization
    
    Args:
        obj: Object that may contain numpy types
    
    Returns:
        Object with numpy types converted to Python types
    """
    if isinstance(obj, (np.integer, np.int_, np.intc, np.intp, np.int8,
                        np.int16, np.int32, np.int64, np.uint8, np.uint16,
                        np.uint32, np.uint64)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float_, np.float16, np.float32, np.float64)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, set):
        return {convert_numpy_types(item) for item in obj}
    else:
        return obj

