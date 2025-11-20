"""
Strategy Engine Module
Handles signal generation, position sizing, and exit conditions
"""
from typing import Dict, Optional, Callable, List, Tuple
import pandas as pd
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class StrategyEngine:
    """Manages strategy signals and position sizing"""
    
    def __init__(
        self,
        entry_logic: Optional[str] = None,
        exit_logic: Optional[str] = None,
        take_profit: Optional[float] = None,
        stop_loss: Optional[float] = None,
        time_based_exit: Optional[int] = None,
        position_sizing_method: str = "fixed-dollar",
        fixed_dollar_amount: Optional[float] = None,
        portfolio_percent: Optional[float] = None,
        risk_percent: Optional[float] = None,
        max_positions: Optional[int] = None,
        eligible_symbols: Optional[str] = None,
        ranking_logic: Optional[str] = None,
        stop_loss_type: str = "fixed-percent",
        use_trailing_stops: bool = False,
        trailing_stop_distance: Optional[float] = None
    ):
        self.entry_logic = entry_logic
        self.exit_logic = exit_logic
        self.take_profit = take_profit
        self.stop_loss = stop_loss
        self.time_based_exit = time_based_exit
        
        self.position_sizing_method = position_sizing_method
        self.fixed_dollar_amount = fixed_dollar_amount
        self.portfolio_percent = portfolio_percent
        self.risk_percent = risk_percent
        self.max_positions = max_positions
        
        self.eligible_symbols = eligible_symbols
        self.ranking_logic = ranking_logic
        
        self.stop_loss_type = stop_loss_type
        self.use_trailing_stops = use_trailing_stops
        self.trailing_stop_distance = trailing_stop_distance
        
        # Compiled signal functions
        self.entry_signal_func: Optional[Callable] = None
        self.exit_signal_func: Optional[Callable] = None
        
        logger.info("Strategy engine initialized")
    
    async def generate_entry_signals_async(
        self,
        market_data: pd.DataFrame,
        timestamp: datetime,
        eligible_tickers: List[str]
    ) -> List[str]:
        """
        Generate entry signals for eligible tickers (async version for FinChat)
        
        Args:
            market_data: Market data DataFrame
            timestamp: Current timestamp
            eligible_tickers: List of eligible ticker symbols
        
        Returns:
            List of tickers with entry signals
        """
        signals = []
        
        for ticker in eligible_tickers:
            try:
                if await self._check_entry_signal_async(market_data, ticker, timestamp):
                    signals.append(ticker)
            except Exception as e:
                logger.error(f"Error checking entry signal for {ticker}: {str(e)}")
                continue
        
        return signals
    
    def generate_entry_signals(
        self,
        market_data: pd.DataFrame,
        timestamp: datetime,
        eligible_tickers: List[str]
    ) -> List[str]:
        """
        Generate entry signals for eligible tickers
        
        Args:
            market_data: Market data DataFrame
            timestamp: Current timestamp
            eligible_tickers: List of eligible ticker symbols
        
        Returns:
            List of tickers with entry signals
        """
        signals = []
        
        for ticker in eligible_tickers:
            try:
                if self._check_entry_signal(market_data, ticker, timestamp):
                    signals.append(ticker)
            except Exception as e:
                logger.error(f"Error checking entry signal for {ticker}: {str(e)}")
                continue
        
        return signals
    
    async def _check_entry_signal_async(
        self,
        market_data: pd.DataFrame,
        ticker: str,
        timestamp: datetime
    ) -> bool:
        """
        Async version of entry signal check (for FinChat COT calls)
        """
        # If custom entry function is provided, check if it's FinChat-based
        if self.entry_signal_func is not None:
            # Check if this is a FinChat function
            if hasattr(self.entry_signal_func, '_is_finchat') and self.entry_signal_func._is_finchat:
                # Call the async function
                if hasattr(self.entry_signal_func, '_async_func'):
                    return await self.entry_signal_func._async_func(market_data, ticker, timestamp)
            else:
                # Regular sync function
                return self.entry_signal_func(market_data, ticker, timestamp)
        
        # If entry logic string is provided but no custom function was set,
        # try default logic (fallback)
        if self.entry_logic:
            logger.debug(f"No custom entry function set, using default logic for {ticker}")
            return self._default_entry_logic(market_data, ticker, timestamp)
        
        # No entry logic defined - return False
        return False
    
    def _check_entry_signal(
        self,
        market_data: pd.DataFrame,
        ticker: str,
        timestamp: datetime
    ) -> bool:
        """
        Check if entry signal is triggered for a ticker
        
        This is a simplified implementation. In production, this would:
        1. Parse the entry_logic string
        2. Evaluate it against market data
        3. Return boolean signal
        """
        # If custom entry function is provided, use it
        if self.entry_signal_func is not None:
            # Check if this is a FinChat function (needs async handling)
            if hasattr(self.entry_signal_func, '_is_finchat') and self.entry_signal_func._is_finchat:
                # For FinChat, we need async handling - return False here, will be handled in async version
                logger.warning("FinChat entry signal detected but called from sync context - use async version")
                return False
            return self.entry_signal_func(market_data, ticker, timestamp)
        
        # If entry logic string is provided but no custom function was set,
        # try default logic (fallback)
        if self.entry_logic:
            logger.debug(f"No custom entry function set, using default logic for {ticker}")
            return self._default_entry_logic(market_data, ticker, timestamp)
        
        # No entry logic defined - return False
        return False
    
    def _default_entry_logic(
        self,
        market_data: pd.DataFrame,
        ticker: str,
        timestamp: datetime
    ) -> bool:
        """Default entry logic - simple example"""
        try:
            # Get recent data for ticker
            ticker_data = market_data.xs(ticker, level='ticker')
            recent_data = ticker_data[ticker_data.index <= timestamp].tail(20)
            
            if len(recent_data) < 20:
                return False
            
            # Simple moving average crossover
            if 'close' in recent_data.columns:
                ma_fast = recent_data['close'].tail(5).mean()
                ma_slow = recent_data['close'].tail(20).mean()
                
                # Entry signal: fast MA crosses above slow MA
                return ma_fast > ma_slow
            
            return False
        except:
            return False
    
    async def check_exit_signal_async(
        self,
        market_data: pd.DataFrame,
        ticker: str,
        timestamp: datetime,
        position: 'Position'
    ) -> Tuple[bool, str]:
        """
        Async version of exit signal check (for FinChat COT calls)
        """
        # Priority order: Stop Loss -> Take Profit -> Time Exit -> Strategy Exit
        
        # 1. Check stop loss
        if self.stop_loss is not None:
            if self._check_stop_loss(position):
                return True, "stop_loss"
        
        # 2. Check trailing stop
        if self.use_trailing_stops and self.trailing_stop_distance is not None:
            if self._check_trailing_stop(position):
                return True, "trailing_stop"
        
        # 3. Check take profit
        if self.take_profit is not None:
            if self._check_take_profit(position):
                return True, "take_profit"
        
        # 4. Check time-based exit
        if self.time_based_exit is not None:
            if self._check_time_exit(position, timestamp):
                return True, "time_exit"
        
        # 5. Check strategy exit signal (may be FinChat-based)
        if await self._check_strategy_exit_async(market_data, ticker, timestamp, position):
            return True, "strategy_signal"
        
        return False, ""
    
    def check_exit_signal(
        self,
        market_data: pd.DataFrame,
        ticker: str,
        timestamp: datetime,
        position: 'Position'
    ) -> Tuple[bool, str]:
        """
        Check if any exit condition is met
        
        Returns:
            (should_exit, exit_reason)
        """
        # Priority order: Stop Loss -> Take Profit -> Time Exit -> Strategy Exit
        
        # 1. Check stop loss
        if self.stop_loss is not None:
            if self._check_stop_loss(position):
                return True, "stop_loss"
        
        # 2. Check trailing stop
        if self.use_trailing_stops and self.trailing_stop_distance is not None:
            if self._check_trailing_stop(position):
                return True, "trailing_stop"
        
        # 3. Check take profit
        if self.take_profit is not None:
            if self._check_take_profit(position):
                return True, "take_profit"
        
        # 4. Check time-based exit
        if self.time_based_exit is not None:
            if self._check_time_exit(position, timestamp):
                return True, "time_exit"
        
        # 5. Check strategy exit signal
        if self._check_strategy_exit(market_data, ticker, timestamp, position):
            return True, "strategy_signal"
        
        return False, ""
    
    def _check_stop_loss(self, position: 'Position') -> bool:
        """Check if stop loss is hit"""
        if self.stop_loss_type == "fixed-percent":
            stop_price = position.entry_price * (1 - self.stop_loss / 100)
            return position.current_price <= stop_price
        elif self.stop_loss_type == "dollar-based":
            # Implement dollar-based stop loss
            pass
        elif self.stop_loss_type == "volatility-based":
            # Implement volatility-based stop loss (ATR)
            pass
        
        return False
    
    def _check_trailing_stop(self, position: 'Position') -> bool:
        """Check if trailing stop is hit"""
        trailing_stop = position.highest_price * (1 - self.trailing_stop_distance / 100)
        return position.current_price <= trailing_stop
    
    def _check_take_profit(self, position: 'Position') -> bool:
        """Check if take profit is hit"""
        take_profit_price = position.entry_price * (1 + self.take_profit / 100)
        return position.current_price >= take_profit_price
    
    def _check_time_exit(self, position: 'Position', timestamp: datetime) -> bool:
        """Check if time-based exit is triggered"""
        days_held = (timestamp - position.entry_timestamp).days
        return days_held >= self.time_based_exit
    
    async def _check_strategy_exit_async(
        self,
        market_data: pd.DataFrame,
        ticker: str,
        timestamp: datetime,
        position: 'Position'
    ) -> bool:
        """Async version of strategy exit check (for FinChat COT calls)"""
        # If custom exit function is provided, check if it's FinChat-based
        if self.exit_signal_func is not None:
            # Check if this is a FinChat function
            if hasattr(self.exit_signal_func, '_is_finchat') and self.exit_signal_func._is_finchat:
                # Call the async function
                if hasattr(self.exit_signal_func, '_async_func'):
                    return await self.exit_signal_func._async_func(market_data, ticker, timestamp, position)
            else:
                # Regular sync function
                return self.exit_signal_func(market_data, ticker, timestamp, position)
        
        # If exit logic string is provided but no custom function was set,
        # try default logic (fallback)
        if self.exit_logic:
            logger.debug(f"No custom exit function set, using default logic for {ticker}")
            return self._default_exit_logic(market_data, ticker, timestamp, position)
        
        return False
    
    def _check_strategy_exit(
        self,
        market_data: pd.DataFrame,
        ticker: str,
        timestamp: datetime,
        position: 'Position'
    ) -> bool:
        """Check if strategy exit signal is triggered"""
        # If custom exit function is provided, use it
        if self.exit_signal_func is not None:
            # Check if this is a FinChat function (needs async handling)
            if hasattr(self.exit_signal_func, '_is_finchat') and self.exit_signal_func._is_finchat:
                # For FinChat, we need async handling - return False here, will be handled in async version
                logger.warning("FinChat exit signal detected but called from sync context - use async version")
                return False
            return self.exit_signal_func(market_data, ticker, timestamp, position)
        
        # If exit logic string is provided but no custom function was set,
        # try default logic (fallback)
        if self.exit_logic:
            logger.debug(f"No custom exit function set, using default logic for {ticker}")
            return self._default_exit_logic(market_data, ticker, timestamp, position)
        
        return False
    
    def _default_exit_logic(
        self,
        market_data: pd.DataFrame,
        ticker: str,
        timestamp: datetime,
        position: 'Position'
    ) -> bool:
        """Default exit logic - simple example"""
        try:
            # Get recent data for ticker
            ticker_data = market_data.xs(ticker, level='ticker')
            recent_data = ticker_data[ticker_data.index <= timestamp].tail(20)
            
            if len(recent_data) < 20:
                return False
            
            # Simple moving average crossover
            if 'close' in recent_data.columns:
                ma_fast = recent_data['close'].tail(5).mean()
                ma_slow = recent_data['close'].tail(20).mean()
                
                # Exit signal: fast MA crosses below slow MA
                return ma_fast < ma_slow
            
            return False
        except:
            return False
    
    def calculate_position_size(
        self,
        ticker: str,
        current_price: float,
        portfolio_value: float,
        cash_available: float
    ) -> float:
        """
        Calculate position size in shares
        
        Returns:
            Number of shares to buy
        """
        if self.position_sizing_method == "fixed-dollar":
            if self.fixed_dollar_amount is None:
                logger.error("Fixed dollar amount not specified")
                return 0.0
            shares = self.fixed_dollar_amount / current_price
        
        elif self.position_sizing_method == "portfolio-percent":
            if self.portfolio_percent is None:
                logger.error("Portfolio percent not specified")
                return 0.0
            position_value = portfolio_value * (self.portfolio_percent / 100)
            shares = position_value / current_price
        
        elif self.position_sizing_method == "risk-based":
            if self.risk_percent is None or self.stop_loss is None:
                logger.error("Risk percent or stop loss not specified")
                return 0.0
            
            # Risk-based position sizing
            risk_amount = portfolio_value * (self.risk_percent / 100)
            stop_distance = current_price * (self.stop_loss / 100)
            shares = risk_amount / stop_distance if stop_distance > 0 else 0.0
        
        else:
            logger.error(f"Unknown position sizing method: {self.position_sizing_method}")
            return 0.0
        
        # Round down to avoid fractional shares (unless fractional trading allowed)
        shares = int(shares)
        
        return shares
    
    def rank_signals(
        self,
        signals: List[str],
        market_data: pd.DataFrame,
        timestamp: datetime,
        max_positions: int
    ) -> List[str]:
        """
        Rank and filter signals if more than max_positions
        
        Args:
            signals: List of tickers with entry signals
            market_data: Market data
            timestamp: Current timestamp
            max_positions: Maximum number of positions to open
        
        Returns:
            Ranked list of tickers (top max_positions)
        """
        if len(signals) <= max_positions:
            return signals
        
        # If ranking logic is provided, use it
        if self.ranking_logic:
            # In production, this would parse and apply custom ranking logic
            pass
        
        # Default: random selection or by liquidity
        # For now, just return first N signals
        return signals[:max_positions]
    
    def filter_eligible_universe(
        self,
        all_tickers: List[str],
        market_data: pd.DataFrame,
        timestamp: datetime
    ) -> List[str]:
        """
        Filter tickers to eligible universe
        
        Args:
            all_tickers: All available tickers
            market_data: Market data
            timestamp: Current timestamp
        
        Returns:
            List of eligible tickers
        """
        # If eligible symbols description is provided, parse it
        if self.eligible_symbols:
            # In production, this would parse natural language description
            # For now, returning all tickers
            pass
        
        # Basic filtering: remove tickers with no data at current timestamp
        eligible = []
        for ticker in all_tickers:
            try:
                if (timestamp, ticker) in market_data.index:
                    eligible.append(ticker)
            except:
                continue
        
        return eligible
    
    def set_entry_signal_function(self, func: Callable):
        """Set custom entry signal function"""
        self.entry_signal_func = func
    
    def set_exit_signal_function(self, func: Callable):
        """Set custom exit signal function"""
        self.exit_signal_func = func

