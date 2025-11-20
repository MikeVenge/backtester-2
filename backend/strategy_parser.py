"""
Strategy Parser Module
Parses natural language strategy descriptions and FinChat COT prompts into executable signal functions
"""
import re
from typing import Callable, Optional, Dict
import pandas as pd
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class StrategyParser:
    """Parses strategy logic strings and FinChat COT prompts into executable functions"""
    
    def __init__(self, finchat_client=None, signal_tracker=None):
        """
        Initialize strategy parser
        
        Args:
            finchat_client: Optional FinChatClient instance for COT execution
            signal_tracker: Optional list to track FinChat signals for monitoring
        """
        self.finchat_client = finchat_client
        self.signal_tracker = signal_tracker  # List to append signals to
        self.backtest_start: Optional[datetime] = None
        self.backtest_end: Optional[datetime] = None
    
    def set_backtest_range(self, start: datetime, end: datetime):
        """Set the backtest date range for time-based strategies"""
        self.backtest_start = start
        self.backtest_end = end
    
    def parse_entry_logic(
        self,
        entry_logic: Optional[str],
        entry_prompt_type: str = "string",
        entry_finchat_slug: Optional[str] = None
    ) -> Optional[Callable]:
        """
        Parse entry logic string or FinChat COT slug into a callable function
        
        Args:
            entry_logic: Natural language description of entry logic (for simple patterns)
            entry_prompt_type: Type of prompt ("string", "url", "finchat-slug")
            entry_finchat_slug: FinChat COT slug identifier
        
        Returns:
            Callable function: (market_data, ticker, timestamp) -> bool
        """
        # Priority: FinChat slug > entry_logic string
        if entry_prompt_type == "finchat-slug" and entry_finchat_slug:
            if not self.finchat_client:
                logger.error("FinChat client not provided but FinChat slug specified")
                return None
            return self._create_finchat_entry(entry_finchat_slug)
        
        if not entry_logic:
            return None
        
        entry_logic_lower = entry_logic.lower().strip()
        
        # Pattern: "Buy on first day" or "Buy on the first day"
        if re.search(r'buy\s+on\s+(the\s+)?first\s+day', entry_logic_lower):
            return self._create_first_day_entry()
        
        # Pattern: "Buy every N days" or "Buy every N business days"
        match = re.search(r'buy\s+every\s+(\d+)\s+(business\s+)?days?', entry_logic_lower)
        if match:
            n_days = int(match.group(1))
            return self._create_every_n_days_entry(n_days)
        
        # Pattern: "Buy immediately" or "Buy now"
        if re.search(r'buy\s+(immediately|now)', entry_logic_lower):
            return self._create_immediate_entry()
        
        logger.warning(f"Could not parse entry logic: {entry_logic}. Using default logic.")
        return None
    
    def parse_exit_logic(
        self,
        exit_logic: Optional[str],
        exit_prompt_type: str = "string",
        exit_finchat_slug: Optional[str] = None,
        upside_threshold: Optional[float] = None,
        downside_threshold: Optional[float] = None
    ) -> Optional[Callable]:
        """
        Parse exit logic string or FinChat COT slug into a callable function
        
        Args:
            exit_logic: Natural language description of exit logic (for simple patterns)
            exit_prompt_type: Type of prompt ("string", "url", "finchat-slug")
            exit_finchat_slug: FinChat COT slug identifier
        
        Returns:
            Callable function: (market_data, ticker, timestamp, position) -> bool
        """
        # Priority: FinChat slug > exit_logic string
        if exit_prompt_type == "finchat-slug" and exit_finchat_slug:
            if not self.finchat_client:
                logger.error("FinChat client not provided but FinChat slug specified")
                return None
            return self._create_finchat_exit(exit_finchat_slug, upside_threshold, downside_threshold)
        
        if not exit_logic:
            return None
        
        exit_logic_lower = exit_logic.lower().strip()
        
        # Pattern: "Hold until end" or "Hold until the end"
        if re.search(r'hold\s+until\s+(the\s+)?end', exit_logic_lower):
            return self._create_hold_until_end_exit()
        
        # Pattern: "Sell after N days" or "Exit after N days"
        match = re.search(r'(sell|exit)\s+after\s+(\d+)\s+days?', exit_logic_lower)
        if match:
            n_days = int(match.group(2))
            return self._create_exit_after_n_days(n_days)
        
        # Pattern: "Never exit" or "Hold forever"
        if re.search(r'(never\s+exit|hold\s+forever)', exit_logic_lower):
            return self._create_never_exit()
        
        logger.warning(f"Could not parse exit logic: {exit_logic}. Using default logic.")
        return None
    
    def _create_finchat_entry(self, cot_slug: str) -> Callable:
        """Create entry function that calls FinChat COT and evaluates result"""
        # Cache results to avoid calling COT multiple times for same ticker/timestamp
        cot_cache: Dict[str, Dict[str, bool]] = {}
        
        async def entry_signal_async(
            market_data: pd.DataFrame,
            ticker: str,
            timestamp: datetime
        ) -> bool:
            # Create cache key
            cache_key = f"{ticker}_{timestamp.date()}"
            
            # Check cache
            if cache_key in cot_cache:
                return cot_cache[cache_key].get("signal", False)
            
            try:
                # Format date as mm/dd/yyyy for FinChat COT
                date_str = timestamp.strftime("%m/%d/%Y")
                
                # Call FinChat COT with required parameters
                logger.info(f"Calling FinChat COT {cot_slug} for entry signal: {ticker} at {timestamp}")
                result = await self.finchat_client.run_cot(
                    cot_slug=cot_slug,
                    ticker=ticker,
                    additional_params={
                        "stock_symbol": ticker,  # Required parameter name
                        "date": date_str  # Date in mm/dd/yyyy format
                    }
                )
                
                # Parse result to get signal
                parsed = self.finchat_client.parse_cot_result(result["content"])
                signal = parsed.get("signal", "hold")
                confidence = parsed.get("confidence", 0.5)
                reasoning = parsed.get("reasoning", "")
                
                # Log detailed information
                print(f"\n{'='*80}")
                print(f"ENTRY SIGNAL - {ticker} @ {timestamp.strftime('%Y-%m-%d')} ({date_str})")
                print(f"{'='*80}")
                print(f"COT Slug: {cot_slug}")
                print(f"Parameters: stock_symbol={ticker}, date={date_str}")
                print(f"Signal: {signal.upper()}")
                print(f"Confidence: {confidence:.2f}")
                print(f"\nCOT Response Content:")
                print(f"{'-'*80}")
                print(result["content"][:1000])  # First 1000 chars
                if len(result["content"]) > 1000:
                    print(f"\n... (truncated, total length: {len(result['content'])} chars)")
                print(f"{'-'*80}")
                print(f"Parsed Reasoning: {reasoning[:200]}")
                print(f"{'='*80}\n")
                
                # Track signal for results
                if self.signal_tracker is not None:
                    self.signal_tracker.append({
                        "type": "entry",
                        "ticker": ticker,
                        "timestamp": timestamp.isoformat(),
                        "date": date_str,  # Date in mm/dd/yyyy format
                        "cot_slug": cot_slug,
                        "signal": signal,
                        "confidence": confidence,
                        "cot_response": result["content"][:2000],  # First 2000 chars
                        "parsed_reasoning": reasoning[:500]
                    })
                
                logger.info(
                    f"FinChat COT entry result for {ticker}: signal={signal}, "
                    f"confidence={confidence:.2f}"
                )
                
                # Cache result
                cot_cache[cache_key] = {
                    "signal": signal == "buy",
                    "confidence": confidence,
                    "reasoning": parsed.get("reasoning", "")
                }
                
                # Return True if signal is "buy"
                return signal == "buy"
                
            except Exception as e:
                logger.error(f"Error calling FinChat COT for entry signal: {e}")
                # On error, return False (don't enter)
                cot_cache[cache_key] = {"signal": False, "error": str(e)}
                return False
        
        # Wrap async function to work with sync interface
        # Note: This will need to be called from async context
        def entry_signal(market_data: pd.DataFrame, ticker: str, timestamp: datetime) -> bool:
            # This is a placeholder - actual async call will be handled in backtest engine
            # For now, return False and let the async wrapper handle it
            return False
        
        # Store async function for later use
        entry_signal._async_func = entry_signal_async
        entry_signal._is_finchat = True
        entry_signal._cot_slug = cot_slug
        
        return entry_signal
    
    def _create_finchat_exit(self, cot_slug: str, upside_threshold: Optional[float] = None, downside_threshold: Optional[float] = None) -> Callable:
        """Create exit function that calls FinChat COT and evaluates result"""
        # Cache results to avoid calling COT multiple times for same ticker/timestamp
        cot_cache: Dict[str, Dict[str, bool]] = {}
        
        async def exit_signal_async(
            market_data: pd.DataFrame,
            ticker: str,
            timestamp: datetime,
            position
        ) -> bool:
            if position is None:
                return False
            
            # Create cache key
            cache_key = f"{ticker}_{timestamp.date()}"
            
            # Check cache
            if cache_key in cot_cache:
                return cot_cache[cache_key].get("signal", False)
            
            try:
                # Get yesterday's price from market data
                yesterday_price = None
                try:
                    ticker_data = market_data.xs(ticker, level='ticker')
                    # Get all timestamps before current timestamp
                    past_timestamps = ticker_data[ticker_data.index < timestamp].index.tolist()
                    if past_timestamps:
                        # Get the most recent timestamp before today
                        yesterday_timestamp = max(past_timestamps)
                        yesterday_row = ticker_data.loc[yesterday_timestamp]
                        # Try to get close price, fallback to adjusted_close
                        yesterday_price = yesterday_row.get('close') or yesterday_row.get('adjusted_close')
                        if pd.isna(yesterday_price):
                            yesterday_price = None
                except Exception as e:
                    logger.warning(f"Could not get yesterday's price for {ticker}: {e}")
                    # If we can't get yesterday's price, use entry price as fallback
                    yesterday_price = position.entry_price
                
                # Get today's price (current price)
                todays_price = position.current_price
                
                # Use thresholds from config, or calculate from entry price if not provided
                upside_thresh = upside_threshold
                downside_thresh = downside_threshold
                
                # If thresholds not provided, use takeProfit/stopLoss if available
                # Or calculate reasonable defaults (e.g., 10% upside, 5% downside)
                if upside_thresh is None:
                    # Could use takeProfit if available, or default
                    upside_thresh = 10.0  # Default 10% upside threshold
                if downside_thresh is None:
                    # Could use stopLoss if available, or default
                    downside_thresh = 5.0  # Default 5% downside threshold
                
                # Call FinChat COT with required parameters
                logger.info(f"Calling FinChat COT {cot_slug} for exit signal: {ticker} at {timestamp}")
                result = await self.finchat_client.run_cot(
                    cot_slug=cot_slug,
                    ticker=ticker,  # Will be mapped to stock_symbol in run_cot
                    additional_params={
                        "stock_symbol": ticker,  # Required parameter name
                        "yesterdays_price": str(yesterday_price) if yesterday_price else str(position.entry_price),
                        "todays_price": str(todays_price),
                        "upside_threshold%": f"{upside_thresh}%",
                        "downside_threshold%": f"{downside_thresh}%"
                    }
                )
                
                # Parse result to get signal
                parsed = self.finchat_client.parse_cot_result(result["content"])
                signal = parsed.get("signal", "hold")
                confidence = parsed.get("confidence", 0.5)
                reasoning = parsed.get("reasoning", "")
                
                # Log detailed information
                print(f"\n{'='*80}")
                print(f"EXIT SIGNAL - {ticker} @ {timestamp.strftime('%Y-%m-%d')}")
                print(f"{'='*80}")
                print(f"COT Slug: {cot_slug}")
                print(f"Position Entry: {position.entry_timestamp.strftime('%Y-%m-%d')} @ ${position.entry_price:.2f}")
                print(f"Yesterday Price: ${yesterday_price:.2f}")
                print(f"Today Price: ${todays_price:.2f}")
                print(f"Upside Threshold: {upside_thresh}%")
                print(f"Downside Threshold: {downside_thresh}%")
                print(f"Signal: {signal.upper()}")
                print(f"Confidence: {confidence:.2f}")
                print(f"\nCOT Response Content:")
                print(f"{'-'*80}")
                print(result["content"][:1000])  # First 1000 chars
                if len(result["content"]) > 1000:
                    print(f"\n... (truncated, total length: {len(result['content'])} chars)")
                print(f"{'-'*80}")
                print(f"Parsed Reasoning: {reasoning[:200]}")
                print(f"{'='*80}\n")
                
                # Track signal for results
                if self.signal_tracker is not None:
                    self.signal_tracker.append({
                        "type": "exit",
                        "ticker": ticker,
                        "timestamp": timestamp.isoformat(),
                        "cot_slug": cot_slug,
                        "position_entry_date": position.entry_timestamp.isoformat(),
                        "position_entry_price": position.entry_price,
                        "yesterday_price": float(yesterday_price) if yesterday_price else None,
                        "today_price": float(todays_price),
                        "upside_threshold": upside_thresh,
                        "downside_threshold": downside_thresh,
                        "signal": signal,
                        "confidence": confidence,
                        "cot_response": result["content"][:2000],  # First 2000 chars
                        "parsed_reasoning": reasoning[:500]
                    })
                
                logger.info(
                    f"FinChat COT exit result for {ticker}: signal={signal}, "
                    f"confidence={confidence:.2f}"
                )
                
                # Cache result
                cot_cache[cache_key] = {
                    "signal": signal in ["sell", "exit"],
                    "confidence": confidence,
                    "reasoning": parsed.get("reasoning", "")
                }
                
                # Return True if signal is "sell" or "exit"
                return signal in ["sell", "exit"]
                
            except Exception as e:
                logger.error(f"Error calling FinChat COT for exit signal: {e}")
                # On error, return False (don't exit)
                cot_cache[cache_key] = {"signal": False, "error": str(e)}
                return False
        
        # Wrap async function to work with sync interface
        def exit_signal(
            market_data: pd.DataFrame,
            ticker: str,
            timestamp: datetime,
            position
        ) -> bool:
            # This is a placeholder - actual async call will be handled in backtest engine
            return False
        
        # Store async function for later use
        exit_signal._async_func = exit_signal_async
        exit_signal._is_finchat = True
        exit_signal._cot_slug = cot_slug
        
        return exit_signal
    
    def _create_first_day_entry(self) -> Callable:
        """Create entry function that triggers on the first trading day"""
        first_timestamp_seen = {}
        first_day_triggered = {}
        
        def entry_signal(market_data: pd.DataFrame, ticker: str, timestamp: datetime) -> bool:
            # Track the first timestamp we see for this ticker
            if ticker not in first_timestamp_seen:
                first_timestamp_seen[ticker] = timestamp
                first_day_triggered[ticker] = True
                logger.info(f"First day entry signal for {ticker} at {timestamp}")
                return True
            
            # Check if this is still the first day (same date as first timestamp)
            first_date = first_timestamp_seen[ticker].date()
            current_date = timestamp.date()
            
            # If we haven't triggered yet and it's still the first day, trigger
            if ticker not in first_day_triggered and current_date == first_date:
                first_day_triggered[ticker] = True
                logger.info(f"First day entry signal for {ticker} at {timestamp}")
                return True
            
            return False
        
        return entry_signal
    
    def _create_every_n_days_entry(self, n_days: int) -> Callable:
        """Create entry function that triggers every N days"""
        last_entry_date = {}
        days_since_last_entry = {}
        
        def entry_signal(market_data: pd.DataFrame, ticker: str, timestamp: datetime) -> bool:
            if ticker not in last_entry_date:
                # First entry
                last_entry_date[ticker] = timestamp
                days_since_last_entry[ticker] = 0
                logger.debug(f"First entry signal for {ticker} at {timestamp}")
                return True
            
            # Calculate days since last entry
            days_diff = (timestamp - last_entry_date[ticker]).days
            
            if days_diff >= n_days:
                last_entry_date[ticker] = timestamp
                days_since_last_entry[ticker] = 0
                logger.debug(f"Every {n_days} days entry signal for {ticker} at {timestamp}")
                return True
            
            return False
        
        return entry_signal
    
    def _create_immediate_entry(self) -> Callable:
        """Create entry function that triggers immediately"""
        triggered = {}
        
        def entry_signal(market_data: pd.DataFrame, ticker: str, timestamp: datetime) -> bool:
            if ticker not in triggered:
                triggered[ticker] = True
                return True
            return False
        
        return entry_signal
    
    def _create_hold_until_end_exit(self) -> Callable:
        """Create exit function that only exits at the end of backtest"""
        def exit_signal(
            market_data: pd.DataFrame,
            ticker: str,
            timestamp: datetime,
            position
        ) -> bool:
            if position is None:
                return False
            
            # Get all timestamps for this ticker
            try:
                ticker_data = market_data.xs(ticker, level='ticker')
                all_timestamps = ticker_data.index.tolist()
                
                if not all_timestamps:
                    return False
                
                # Check if this is the last timestamp
                last_timestamp = max(all_timestamps)
                
                # Exit if we're at or past the last timestamp
                if timestamp >= last_timestamp:
                    logger.info(f"Hold until end exit signal for {ticker} at {timestamp} (last timestamp: {last_timestamp})")
                    return True
            except Exception as e:
                logger.warning(f"Error checking hold until end for {ticker}: {e}")
                # Fallback: check against backtest_end if available
                if self.backtest_end and timestamp.date() >= self.backtest_end.date():
                    return True
            
            return False
        
        return exit_signal
    
    def _create_exit_after_n_days(self, n_days: int) -> Callable:
        """Create exit function that exits after N days"""
        def exit_signal(
            market_data: pd.DataFrame,
            ticker: str,
            timestamp: datetime,
            position
        ) -> bool:
            if position is None:
                return False
            
            days_held = (timestamp - position.entry_timestamp).days
            if days_held >= n_days:
                logger.debug(f"Exit after {n_days} days signal for {ticker} at {timestamp}")
                return True
            return False
        
        return exit_signal
    
    def _create_never_exit(self) -> Callable:
        """Create exit function that never exits (except at end of backtest)"""
        def exit_signal(
            market_data: pd.DataFrame,
            ticker: str,
            timestamp: datetime,
            position
        ) -> bool:
            # Only exit at the very end
            if self.backtest_end and timestamp >= self.backtest_end:
                return True
            return False
        
        return exit_signal


def parse_strategy_logic(
    entry_logic: Optional[str],
    exit_logic: Optional[str],
    backtest_start: Optional[datetime] = None,
    backtest_end: Optional[datetime] = None,
    finchat_client=None,
    entry_prompt_type: str = "string",
    exit_prompt_type: str = "string",
    entry_finchat_slug: Optional[str] = None,
    exit_finchat_slug: Optional[str] = None,
    upside_threshold: Optional[float] = None,
    downside_threshold: Optional[float] = None,
    signal_tracker: Optional[List] = None
) -> tuple[Optional[Callable], Optional[Callable]]:
    """
    Parse entry and exit logic strings or FinChat COT slugs into executable functions
    
    Args:
        entry_logic: Entry logic string (for simple patterns)
        exit_logic: Exit logic string (for simple patterns)
        backtest_start: Start date of backtest
        backtest_end: End date of backtest
        finchat_client: Optional FinChatClient instance
        entry_prompt_type: Type of entry prompt ("string", "url", "finchat-slug")
        exit_prompt_type: Type of exit prompt ("string", "url", "finchat-slug")
        entry_finchat_slug: FinChat COT slug for entry logic
        exit_finchat_slug: FinChat COT slug for exit logic
    
    Returns:
        Tuple of (entry_function, exit_function)
    """
    parser = StrategyParser(finchat_client=finchat_client, signal_tracker=signal_tracker)
    
    if backtest_start and backtest_end:
        parser.set_backtest_range(backtest_start, backtest_end)
    
    entry_func = parser.parse_entry_logic(
        entry_logic=entry_logic,
        entry_prompt_type=entry_prompt_type,
        entry_finchat_slug=entry_finchat_slug
    )
    
    exit_func = parser.parse_exit_logic(
        exit_logic=exit_logic,
        exit_prompt_type=exit_prompt_type,
        exit_finchat_slug=exit_finchat_slug,
        upside_threshold=upside_threshold,
        downside_threshold=downside_threshold
    )
    
    return entry_func, exit_func
