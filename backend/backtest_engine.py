"""
Backtest Engine Module
Main backtesting execution engine that orchestrates all components
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging

from .portfolio import Portfolio, Position
from .strategy import StrategyEngine
from .data_fetcher import DataFetcher
from .performance import PerformanceAnalyzer
from .utils import (
    calculate_total_cost,
    get_execution_price,
    is_trading_day,
    apply_borrow_cost,
    get_week_start
)

logger = logging.getLogger(__name__)


class BacktestEngine:
    """Main backtesting engine"""
    
    def __init__(self, config: Dict):
        """
        Initialize backtest engine with configuration
        
        Args:
            config: Backtest configuration dictionary
        """
        self.config = config
        self.market_data: Optional[pd.DataFrame] = None
        self.corporate_actions: Dict = {}
        self.benchmark_data: Optional[pd.DataFrame] = None
        
        # Initialize components
        self._initialize_components()
        
        logger.info("Backtest engine initialized")
    
    def _initialize_components(self):
        """Initialize all backtest components"""
        # Initialize FinChat signals tracker early (needed before parse_strategy_logic)
        self.finchat_signals: List[Dict] = []
        
        # Market data config
        md_config = self.config.get('marketData', {})
        
        # Portfolio config
        pr_config = self.config.get('portfolioRisk', {})
        
        # Strategy config
        st_config = self.config.get('strategy', {})
        
        # Trading execution config
        te_config = self.config.get('tradingExecution', {})
        
        # MTM config
        mtm_config = self.config.get('mtm', {})
        
        # Rebalancing config
        rb_config = self.config.get('rebalancing', {})
        
        # Initialize portfolio
        self.portfolio = Portfolio(
            initial_capital=pr_config.get('initialCapital', 10000),
            leverage_allowed=pr_config.get('leverageAllowed', False),
            max_leverage=pr_config.get('maxLeverage', 1.0),
            max_single_asset_percent=pr_config.get('maxSingleAssetPercent'),
            max_sector_percent=pr_config.get('maxSectorPercent'),
            max_net_exposure=pr_config.get('maxNetExposure')
        )
        
        # Initialize strategy engine
        self.strategy = StrategyEngine(
            entry_logic=st_config.get('entryLogic'),
            exit_logic=st_config.get('exitLogic'),
            take_profit=st_config.get('takeProfit'),
            stop_loss=st_config.get('stopLoss'),
            time_based_exit=st_config.get('timeBasedExit'),
            position_sizing_method=st_config.get('positionSizingMethod', 'fixed-dollar'),
            fixed_dollar_amount=st_config.get('fixedDollarAmount'),
            portfolio_percent=st_config.get('portfolioPercent'),
            risk_percent=st_config.get('riskPercent'),
            max_positions=st_config.get('maxPositions'),
            eligible_symbols=st_config.get('eligibleSymbols'),
            ranking_logic=st_config.get('rankingLogic'),
            stop_loss_type=pr_config.get('stopLossType', 'fixed-percent'),
            use_trailing_stops=pr_config.get('useTrailingStops', False),
            trailing_stop_distance=pr_config.get('trailingStopDistance')
        )
        
        # Initialize FinChat client if FinChat slugs are provided
        finchat_client = None
        entry_prompt_type = st_config.get('entryPromptType', 'string')
        exit_prompt_type = st_config.get('exitPromptType', 'string')
        
        if entry_prompt_type == 'finchat-slug' or exit_prompt_type == 'finchat-slug':
            try:
                from .finchat_client import FinChatClient
                finchat_client = FinChatClient()
                logger.info("FinChat client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize FinChat client: {e}")
                logger.warning("Continuing without FinChat - will use fallback logic")
        
        # Parse strategy logic strings or FinChat COT slugs into executable functions
        from .strategy_parser import parse_strategy_logic
        
        # Convert date strings to datetime objects
        backtest_start = None
        backtest_end = None
        if md_config.get('startDate'):
            backtest_start = pd.to_datetime(md_config.get('startDate')).to_pydatetime()
        if md_config.get('endDate'):
            backtest_end = pd.to_datetime(md_config.get('endDate')).to_pydatetime()
        
        entry_func, exit_func = parse_strategy_logic(
            entry_logic=st_config.get('entryLogic') or st_config.get('entryFinChatPrompt'),
            exit_logic=st_config.get('exitLogic') or st_config.get('exitFinChatPrompt'),
            backtest_start=backtest_start,
            backtest_end=backtest_end,
            finchat_client=finchat_client,
            entry_prompt_type=entry_prompt_type,
            exit_prompt_type=exit_prompt_type,
            entry_finchat_slug=st_config.get('entryFinChatSlug'),
            exit_finchat_slug=st_config.get('exitFinChatSlug'),
            upside_threshold=st_config.get('upsideThreshold'),
            downside_threshold=st_config.get('downsideThreshold'),
            signal_tracker=self.finchat_signals
        )
        
        # Store FinChat client for async calls
        self.finchat_client = finchat_client
        
        # Set parsed functions if available
        if entry_func:
            self.strategy.set_entry_signal_function(entry_func)
            entry_desc = st_config.get('entryFinChatSlug') or st_config.get('entryLogic') or st_config.get('entryFinChatPrompt')
            logger.info(f"Using parsed entry logic function: {entry_desc}")
        if exit_func:
            self.strategy.set_exit_signal_function(exit_func)
            exit_desc = st_config.get('exitFinChatSlug') or st_config.get('exitLogic') or st_config.get('exitFinChatPrompt')
            logger.info(f"Using parsed exit logic function: {exit_desc}")
        
        # Initialize data fetcher with AlphaVantage MCP client
        from .av_mcp_client import AlphaVantageMCPClient
        try:
            av_client = AlphaVantageMCPClient()
        except Exception as exc:
            logger.error(f"Failed to initialize AlphaVantage client: {exc}")
            av_client = None
        self.data_fetcher = DataFetcher(alphavantage_client=av_client)
        
        # Initialize performance analyzer
        self.performance = PerformanceAnalyzer()
        
        # Store settings
        self.entry_timing = te_config.get('entryTiming', 'next-bar-open')
        self.commission_type = te_config.get('commissionType', 'per-trade')
        self.commission_amount = te_config.get('commissionAmount', 0)
        self.exchange_fees = te_config.get('exchangeFees', 0)
        self.slippage = te_config.get('slippage', 0)
        self.trading_days = te_config.get('tradingDays', [])
        self.handle_missing_data = te_config.get('handleMissingData', 'skip')
        self.short_selling_allowed = te_config.get('shortSellingAllowed', False)
        self.borrow_cost = te_config.get('borrowCost', 0)
        
        self.mtm_frequency = mtm_config.get('mtmFrequency', 'every-bar')
        self.mtm_price = mtm_config.get('mtmPrice', 'close')
        self.book_dividend_cashflows = mtm_config.get('bookDividendCashflows', False)
        
        self.max_daily_drawdown = pr_config.get('maxDailyDrawdown')
        self.max_weekly_drawdown = pr_config.get('maxWeeklyDrawdown')
        
        # Rebalancing settings
        self.rebalancing_type = rb_config.get('rebalancingType')
        self.drop_delisted = rb_config.get('dropDelisted', False)
        
        # Pending orders (for next-bar-open execution)
        self.pending_entry_orders: List[Dict] = []
        self.pending_exit_orders: List[Dict] = []
    
    async def run(self) -> Dict:
        """
        Execute the backtest
        
        Returns:
            Dictionary with backtest results
        """
        logger.info("Starting backtest execution")
        
        try:
            # Phase 1: Data Acquisition
            await self._fetch_market_data()
            
            # Phase 2: Backtest Execution Loop
            await self._execute_backtest_loop()
            
            # Phase 3: Results Generation
            results = self._generate_results()
            
            logger.info("Backtest completed successfully")
            return results
            
        except Exception as e:
            logger.error(f"Backtest failed: {str(e)}")
            raise
    
    async def _fetch_market_data(self):
        """Fetch and prepare market data"""
        logger.info("Fetching market data")
        
        md_config = self.config.get('marketData', {})
        
        # Parse tickers
        tickers_str = md_config.get('tickers', '')
        tickers = [t.strip().upper() for t in tickers_str.split(',') if t.strip()]
        
        # Parse dates
        start_date = pd.to_datetime(md_config.get('startDate'))
        end_date = pd.to_datetime(md_config.get('endDate'))
        
        # Fetch data
        self.market_data, self.corporate_actions = await self.data_fetcher.fetch_market_data(
            tickers=tickers,
            start_date=start_date,
            end_date=end_date,
            frequency=md_config.get('frequency', 'daily'),
            fields=md_config.get('fields', ['open', 'high', 'low', 'close', 'volume']),
            include_dividends=md_config.get('includeDividends', False),
            include_splits=md_config.get('includeSplits', False),
            include_delistings=md_config.get('includeDelistings', False)
        )
        
        # Handle missing data
        self.market_data = self.data_fetcher.handle_missing_data(
            self.market_data,
            self.handle_missing_data
        )
        
        # Fetch benchmark if specified
        benchmark = md_config.get('benchmark')
        if benchmark:
            await self._fetch_benchmark_data(benchmark, start_date, end_date, md_config.get('frequency', 'daily'))
        
        logger.info(f"Market data loaded: {len(self.market_data)} rows")
    
    async def _fetch_benchmark_data(self, benchmark: str, start_date, end_date, frequency):
        """Fetch benchmark data"""
        try:
            self.benchmark_data, _ = await self.data_fetcher.fetch_market_data(
                tickers=[benchmark],
                start_date=start_date,
                end_date=end_date,
                frequency=frequency,
                fields=['close'],
                include_dividends=False,
                include_splits=False,
                include_delistings=False
            )
            logger.info(f"Benchmark data loaded for {benchmark}")
        except Exception as e:
            logger.warning(f"Could not load benchmark data: {str(e)}")
            self.benchmark_data = None
    
    async def _execute_backtest_loop(self):
        """Main backtest execution loop"""
        logger.info("Executing backtest loop")
        
        # Get unique timestamps
        timestamps = sorted(self.market_data.index.get_level_values('timestamp').unique())
        
        # Track current week for weekly resets
        current_week_start = None
        
        for i, timestamp in enumerate(timestamps):
            # Check if trading day
            if not is_trading_day(timestamp, self.trading_days):
                continue
            
            # Get market data for current timestamp
            try:
                current_data = self.market_data.xs(timestamp, level='timestamp')
            except:
                logger.warning(f"No data available for {timestamp}")
                continue
            
            # PHASE 1: Pre-Processing
            logger.debug(f"Processing timestamp: {timestamp}")
            
            # Reset daily/weekly peaks
            if i > 0:
                prev_timestamp = timestamps[i-1]
                if prev_timestamp.date() != timestamp.date():
                    self.portfolio.reset_daily_peak()
                
                week_start = get_week_start(timestamp)
                if current_week_start is None or week_start != current_week_start:
                    self.portfolio.reset_weekly_peak()
                    current_week_start = week_start
            
            # PHASE 2: Execute Pending Orders from Previous Bar
            if self.entry_timing == 'next-bar-open':
                await self._execute_pending_orders(timestamp, current_data)
            
            # PHASE 3: Mark-to-Market
            if self._should_mtm(timestamp, i):
                self._update_mtm(timestamp, current_data)
            
            # PHASE 4: Handle Dividends
            if self.book_dividend_cashflows:
                self._process_dividends(timestamp)
            
            # PHASE 5: Apply Borrow Costs for Short Positions
            if self.short_selling_allowed:
                self._apply_borrow_costs()
            
            # PHASE 6: Risk Monitoring
            limit_exceeded, reason = self.portfolio.check_drawdown_limits(
                self.max_daily_drawdown,
                self.max_weekly_drawdown
            )
            if limit_exceeded:
                logger.warning(f"Drawdown limit exceeded: {reason}")
                # Continue but don't open new positions
            
            # PHASE 7: Rebalancing Check (if applicable)
            # Simplified - full implementation would check rebalancing conditions
            
            # PHASE 8: Exit Signal Processing
            await self._process_exits(timestamp, current_data)
            
            # PHASE 9: Entry Signal Processing
            await self._process_entries(timestamp, current_data)
        
        logger.info("Backtest loop completed")
    
    def _should_mtm(self, timestamp: datetime, bar_index: int) -> bool:
        """Check if MTM should be performed"""
        if self.mtm_frequency == 'every-bar':
            return True
        elif self.mtm_frequency == 'daily':
            # MTM at end of each day
            return True
        elif self.mtm_frequency == 'weekly':
            # MTM on last bar of week
            return timestamp.weekday() == 4  # Friday
        elif self.mtm_frequency == 'monthly':
            # MTM on last bar of month
            return timestamp.day == 1 or bar_index == 0
        return True
    
    def _update_mtm(self, timestamp: datetime, current_data: pd.DataFrame):
        """Update mark-to-market prices and portfolio value"""
        # Update prices for all positions
        prices = {}
        for ticker in self.portfolio.positions.keys():
            if ticker in current_data.index:
                ticker_data = current_data.loc[ticker]
                price = self._get_mtm_price(ticker_data)
                if price is not None and price > 0:
                    prices[ticker] = price
        
        self.portfolio.update_position_prices(prices)
        self.portfolio.update_portfolio_value(timestamp)
    
    def _get_mtm_price(self, ticker_data: pd.Series) -> Optional[float]:
        """Get MTM price based on settings"""
        if self.mtm_price == 'close':
            return ticker_data.get('close')
        elif self.mtm_price == 'vwap':
            # Use close as proxy for VWAP
            return ticker_data.get('close')
        elif self.mtm_price == 'mid':
            high = ticker_data.get('high')
            low = ticker_data.get('low')
            if high is not None and low is not None:
                return (high + low) / 2
        elif self.mtm_price == 'last':
            return ticker_data.get('close')
        else:
            return ticker_data.get('close')
    
    def _process_dividends(self, timestamp: datetime):
        """Process dividend payments"""
        dividends = self.corporate_actions.get('dividends', {})
        
        for ticker, div_data in dividends.items():
            if ticker not in self.portfolio.positions:
                continue
            
            # Check if any dividend goes ex on this date
            # Simplified - would need proper dividend data structure
            pass
    
    def _apply_borrow_costs(self):
        """Apply borrow costs to short positions"""
        for ticker, position in self.portfolio.positions.items():
            if position.shares < 0:  # Short position
                cost = apply_borrow_cost(
                    abs(position.current_value),
                    self.borrow_cost,
                    days_held=1
                )
                self.portfolio.cash -= cost
    
    async def _process_exits(self, timestamp: datetime, current_data: pd.DataFrame):
        """Process exit signals for existing positions"""
        positions_to_close = []
        
        for ticker, position in self.portfolio.positions.items():
            # Check exit conditions (use async version if FinChat is enabled)
            if self.finchat_client:
                should_exit, exit_reason = await self.strategy.check_exit_signal_async(
                    self.market_data,
                    ticker,
                    timestamp,
                    position
                )
            else:
                should_exit, exit_reason = self.strategy.check_exit_signal(
                    self.market_data,
                    ticker,
                    timestamp,
                    position
                )
            
            if should_exit:
                positions_to_close.append((ticker, exit_reason))
        
        # Execute exits
        for ticker, exit_reason in positions_to_close:
            if self.entry_timing == 'next-bar-open':
                # Queue for next bar
                self.pending_exit_orders.append({
                    'ticker': ticker,
                    'reason': exit_reason
                })
            else:
                # Execute immediately
                await self._execute_exit(ticker, timestamp, current_data, exit_reason)
    
    async def _execute_exit(
        self,
        ticker: str,
        timestamp: datetime,
        current_data: pd.DataFrame,
        exit_reason: str
    ):
        """Execute an exit order"""
        if ticker not in self.portfolio.positions:
            return
        
        position = self.portfolio.positions[ticker]
        
        # Get ticker data
        if ticker not in current_data.index:
            logger.warning(f"No data for {ticker} at {timestamp}")
            return
        
        ticker_data = current_data.loc[ticker]
        
        # Get execution price
        exit_price = get_execution_price(ticker_data.to_dict(), self.entry_timing)
        if exit_price is None or exit_price <= 0:
            return
        
        # Calculate proceeds including costs
        execution_price, exit_proceeds, total_fees = calculate_total_cost(
            position.shares,
            exit_price,
            self.commission_type,
            self.commission_amount,
            self.exchange_fees,
            self.slippage,
            is_buy=False
        )
        
        # Close position
        self.portfolio.close_position(
            ticker,
            execution_price,
            timestamp,
            exit_proceeds,
            exit_reason
        )
    
    async def _process_entries(self, timestamp: datetime, current_data: pd.DataFrame):
        """Process entry signals for new positions"""
        # Check if we can open new positions
        if self.portfolio.trading_halted:
            return
        
        if self.strategy.max_positions is not None:
            if len(self.portfolio.positions) >= self.strategy.max_positions:
                return
        
        # Get all tickers
        all_tickers = current_data.index.tolist()
        
        # Filter to eligible universe
        eligible_tickers = self.strategy.filter_eligible_universe(
            all_tickers,
            self.market_data,
            timestamp
        )
        
        # Remove tickers we already have positions in
        eligible_tickers = [t for t in eligible_tickers if t not in self.portfolio.positions]
        
        # Generate entry signals (use async version if FinChat is enabled)
        if self.finchat_client:
            signals = await self.strategy.generate_entry_signals_async(
                self.market_data,
                timestamp,
                eligible_tickers
            )
        else:
            signals = self.strategy.generate_entry_signals(
                self.market_data,
                timestamp,
                eligible_tickers
            )
        
        if not signals:
            return
        
        # Rank signals if more than available slots
        available_slots = self.strategy.max_positions - len(self.portfolio.positions) if self.strategy.max_positions else len(signals)
        ranked_signals = self.strategy.rank_signals(
            signals,
            self.market_data,
            timestamp,
            available_slots
        )
        
        # Execute entries
        for ticker in ranked_signals:
            if self.entry_timing == 'next-bar-open':
                # Queue for next bar
                self.pending_entry_orders.append({
                    'ticker': ticker,
                    'timestamp': timestamp
                })
            else:
                # Execute immediately
                await self._execute_entry(ticker, timestamp, current_data)
    
    async def _execute_entry(
        self,
        ticker: str,
        timestamp: datetime,
        current_data: pd.DataFrame
    ):
        """Execute an entry order"""
        logger.info(f"Attempting to execute entry for {ticker} at {timestamp}")
        
        # Get ticker data
        if ticker not in current_data.index:
            logger.warning(f"No data for {ticker} at {timestamp}")
            return
        
        ticker_data = current_data.loc[ticker]
        logger.debug(f"Ticker data for {ticker}: {ticker_data.to_dict()}")
        
        # Get execution price
        entry_price = get_execution_price(ticker_data.to_dict(), self.entry_timing)
        if entry_price is None or entry_price <= 0:
            logger.warning(f"Invalid entry price for {ticker}: {entry_price}")
            return
        
        logger.info(f"Entry price for {ticker}: ${entry_price:.2f}")
        
        # Calculate position size
        shares = self.strategy.calculate_position_size(
            ticker,
            entry_price,
            self.portfolio.portfolio_value,
            self.portfolio.cash
        )
        
        logger.info(f"Calculated position size for {ticker}: {shares} shares (portfolio_value=${self.portfolio.portfolio_value:,.2f}, cash=${self.portfolio.cash:,.2f})")
        
        if shares <= 0:
            logger.warning(f"Position size is 0 or negative for {ticker}. Position sizing method: {self.strategy.position_sizing_method}, portfolio_percent: {self.strategy.portfolio_percent}")
            return
        
        # Calculate total cost including fees
        execution_price, total_cost, total_fees = calculate_total_cost(
            shares,
            entry_price,
            self.commission_type,
            self.commission_amount,
            self.exchange_fees,
            self.slippage,
            is_buy=True
        )
        
        # Check if we can open this position
        can_open, reason = self.portfolio.can_open_position(ticker, total_cost)
        if not can_open:
            logger.warning(f"Cannot open position in {ticker}: {reason} (total_cost=${total_cost:,.2f}, buying_power=${self.portfolio.buying_power:,.2f})")
            return
        
        # Check if we have enough cash/buying power
        if total_cost > self.portfolio.buying_power:
            logger.warning(f"Insufficient buying power for {ticker}: need ${total_cost:,.2f}, have ${self.portfolio.buying_power:,.2f}")
            return
        
        logger.info(f"Opening position: {ticker} - {shares} shares @ ${execution_price:.2f}, total cost: ${total_cost:,.2f}")
        
        # Open position
        success = self.portfolio.open_position(
            ticker,
            shares,
            execution_price,
            timestamp,
            total_cost
        )
        
        if success:
            logger.info(f"Successfully opened position: {ticker} - {shares} shares @ ${execution_price:.2f}")
        else:
            logger.error(f"Failed to open position: {ticker}")
    
    async def _execute_pending_orders(self, timestamp: datetime, current_data: pd.DataFrame):
        """Execute orders that were pending from previous bar"""
        # Execute pending exits first
        for order in self.pending_exit_orders:
            await self._execute_exit(
                order['ticker'],
                timestamp,
                current_data,
                order['reason']
            )
        self.pending_exit_orders.clear()
        
        # Execute pending entries
        for order in self.pending_entry_orders:
            await self._execute_entry(
                order['ticker'],
                timestamp,
                current_data
            )
        self.pending_entry_orders.clear()
    
    def _generate_results(self) -> Dict:
        """Generate backtest results"""
        logger.info("Generating results")
        
        # Calculate performance metrics
        benchmark_returns = None
        if self.benchmark_data is not None:
            benchmark_returns = self.benchmark_data['close'].pct_change()
        
        metrics = self.performance.calculate_all_metrics(
            self.portfolio.equity_curve,
            self.portfolio.closed_trades,
            self.portfolio.initial_capital,
            benchmark_returns
        )
        
        # Generate equity curve
        equity_curve = [
            {'date': ts.isoformat(), 'value': round(val, 2)}
            for ts, val in self.portfolio.equity_curve
        ]
        
        # Export trade log
        trade_log_df = self.performance.export_trade_log(self.portfolio.closed_trades)
        trades = trade_log_df.to_dict('records') if not trade_log_df.empty else []
        
        # Compile results
        results = {
            'status': 'success',
            'summary': {
                **metrics['basic_metrics'],
                **metrics['ratio_metrics'],
                **metrics['trade_stats']
            },
            'equity_curve': equity_curve,
            'trades': trades,
            'positions': self.portfolio.get_position_summary()['positions'],
            'benchmark_comparison': metrics.get('benchmark_metrics', {}),
            'finchat_signals': self.finchat_signals  # Include FinChat COT signals
        }
        
        return results

