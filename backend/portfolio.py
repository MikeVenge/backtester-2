"""
Portfolio Management Module
Handles portfolio state, positions, cash, and risk limits
"""
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class Position:
    """Represents a single position in the portfolio"""
    ticker: str
    shares: float
    entry_price: float
    entry_timestamp: datetime
    entry_cost: float  # Including commissions and fees
    highest_price: float  # For trailing stops
    current_price: float = 0.0
    
    @property
    def current_value(self) -> float:
        """Current market value of position"""
        return self.shares * self.current_price
    
    @property
    def unrealized_pnl(self) -> float:
        """Unrealized P&L"""
        return (self.current_price - self.entry_price) * self.shares
    
    @property
    def unrealized_pnl_percent(self) -> float:
        """Unrealized P&L as percentage"""
        if self.entry_price == 0:
            return 0.0
        return ((self.current_price - self.entry_price) / self.entry_price) * 100
    
    @property
    def days_held(self) -> int:
        """Number of days position has been held"""
        return (datetime.now() - self.entry_timestamp).days


@dataclass
class Trade:
    """Represents a closed trade"""
    ticker: str
    entry_date: datetime
    entry_price: float
    exit_date: datetime
    exit_price: float
    shares: float
    pnl: float
    pnl_percent: float
    entry_cost: float
    exit_cost: float
    holding_period_days: int
    exit_reason: str = ""


class Portfolio:
    """Manages portfolio state and operations"""
    
    def __init__(
        self,
        initial_capital: float,
        leverage_allowed: bool = False,
        max_leverage: float = 1.0,
        max_single_asset_percent: Optional[float] = None,
        max_sector_percent: Optional[float] = None,
        max_net_exposure: Optional[float] = None
    ):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.leverage_allowed = leverage_allowed
        self.max_leverage = max_leverage
        self.max_single_asset_percent = max_single_asset_percent
        self.max_sector_percent = max_sector_percent
        self.max_net_exposure = max_net_exposure
        
        # Position tracking
        self.positions: Dict[str, Position] = {}
        self.closed_trades: List[Trade] = []
        
        # Value tracking
        self.portfolio_value = initial_capital
        self.peak_value = initial_capital
        self.peak_value_today = initial_capital
        self.peak_value_this_week = initial_capital
        
        # Equity curve
        self.equity_curve: List[Tuple[datetime, float]] = []
        
        # Trading state
        self.trading_halted = False
        
        logger.info(f"Portfolio initialized with ${initial_capital:,.2f}")
    
    @property
    def total_position_value(self) -> float:
        """Total value of all positions"""
        return sum(pos.current_value for pos in self.positions.values())
    
    @property
    def total_unrealized_pnl(self) -> float:
        """Total unrealized P&L"""
        return sum(pos.unrealized_pnl for pos in self.positions.values())
    
    @property
    def current_leverage(self) -> float:
        """Current leverage ratio"""
        if self.portfolio_value == 0:
            return 0.0
        return abs(self.total_position_value) / self.portfolio_value
    
    @property
    def buying_power(self) -> float:
        """Available buying power"""
        if self.leverage_allowed:
            return self.portfolio_value * self.max_leverage - self.total_position_value
        return self.cash
    
    def update_portfolio_value(self, timestamp: datetime) -> float:
        """
        Update portfolio value based on current positions
        
        Returns:
            Current portfolio value
        """
        self.portfolio_value = self.cash + self.total_position_value
        
        # Update peaks
        if self.portfolio_value > self.peak_value:
            self.peak_value = self.portfolio_value
        if self.portfolio_value > self.peak_value_today:
            self.peak_value_today = self.portfolio_value
        if self.portfolio_value > self.peak_value_this_week:
            self.peak_value_this_week = self.portfolio_value
        
        # Record in equity curve
        self.equity_curve.append((timestamp, self.portfolio_value))
        
        logger.debug(f"Portfolio value: ${self.portfolio_value:,.2f}, Cash: ${self.cash:,.2f}, Positions: {len(self.positions)}")
        
        return self.portfolio_value
    
    def update_position_prices(self, prices: Dict[str, float]):
        """Update current prices for all positions"""
        for ticker, position in self.positions.items():
            if ticker in prices:
                position.current_price = prices[ticker]
                
                # Update highest price for trailing stops
                if prices[ticker] > position.highest_price:
                    position.highest_price = prices[ticker]
    
    def can_open_position(
        self, 
        ticker: str, 
        position_value: float,
        sector: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Check if we can open a new position given risk limits
        
        Returns:
            (can_open, reason)
        """
        # Check if trading is halted
        if self.trading_halted:
            return False, "Trading is halted due to drawdown limits"
        
        # Check single asset limit
        if self.max_single_asset_percent is not None:
            max_position_value = self.portfolio_value * (self.max_single_asset_percent / 100)
            if position_value > max_position_value:
                return False, f"Position size exceeds max single asset limit ({self.max_single_asset_percent}%)"
        
        # Check leverage limit
        if not self.leverage_allowed and position_value > self.cash:
            return False, "Insufficient cash and leverage not allowed"
        
        if self.leverage_allowed:
            new_leverage = (self.total_position_value + position_value) / self.portfolio_value
            if new_leverage > self.max_leverage:
                return False, f"Would exceed max leverage ({self.max_leverage}x)"
        
        # Check net exposure
        if self.max_net_exposure is not None:
            new_exposure = ((self.total_position_value + position_value) / self.portfolio_value) * 100
            if new_exposure > self.max_net_exposure:
                return False, f"Would exceed max net exposure ({self.max_net_exposure}%)"
        
        # Check sector limit (if provided)
        if sector and self.max_sector_percent is not None:
            sector_exposure = self._calculate_sector_exposure(sector)
            new_sector_exposure = ((sector_exposure + position_value) / self.portfolio_value) * 100
            if new_sector_exposure > self.max_sector_percent:
                return False, f"Would exceed max sector exposure ({self.max_sector_percent}%)"
        
        return True, "OK"
    
    def open_position(
        self,
        ticker: str,
        shares: float,
        entry_price: float,
        entry_timestamp: datetime,
        total_cost: float
    ) -> bool:
        """
        Open a new position
        
        Args:
            ticker: Ticker symbol
            shares: Number of shares (positive for long, negative for short)
            entry_price: Entry price per share
            entry_timestamp: Timestamp of entry
            total_cost: Total cost including commissions and fees
        
        Returns:
            True if position opened successfully
        """
        if ticker in self.positions:
            logger.warning(f"Position already exists for {ticker}, adding to existing position")
            # Add to existing position
            existing = self.positions[ticker]
            total_shares = existing.shares + shares
            avg_price = ((existing.shares * existing.entry_price) + (shares * entry_price)) / total_shares
            
            existing.shares = total_shares
            existing.entry_price = avg_price
            existing.entry_cost += total_cost
        else:
            # Create new position
            position = Position(
                ticker=ticker,
                shares=shares,
                entry_price=entry_price,
                entry_timestamp=entry_timestamp,
                entry_cost=total_cost,
                highest_price=entry_price,
                current_price=entry_price
            )
            self.positions[ticker] = position
        
        # Deduct cost from cash
        self.cash -= total_cost
        
        logger.info(f"Opened position: {ticker} - {shares} shares @ ${entry_price:.2f}")
        return True
    
    def close_position(
        self,
        ticker: str,
        exit_price: float,
        exit_timestamp: datetime,
        exit_proceeds: float,
        exit_reason: str = ""
    ) -> Optional[Trade]:
        """
        Close an existing position
        
        Args:
            ticker: Ticker symbol
            exit_price: Exit price per share
            exit_timestamp: Timestamp of exit
            exit_proceeds: Net proceeds after commissions and fees
            exit_reason: Reason for exit
        
        Returns:
            Trade object if successful, None otherwise
        """
        if ticker not in self.positions:
            logger.error(f"Cannot close position - {ticker} not in portfolio")
            return None
        
        position = self.positions[ticker]
        
        # Calculate P&L
        pnl = exit_proceeds - position.entry_cost
        pnl_percent = ((exit_price - position.entry_price) / position.entry_price) * 100
        
        # Calculate holding period
        holding_period = (exit_timestamp - position.entry_timestamp).days
        
        # Create trade record
        trade = Trade(
            ticker=ticker,
            entry_date=position.entry_timestamp,
            entry_price=position.entry_price,
            exit_date=exit_timestamp,
            exit_price=exit_price,
            shares=position.shares,
            pnl=pnl,
            pnl_percent=pnl_percent,
            entry_cost=position.entry_cost,
            exit_cost=position.entry_cost + position.shares * exit_price - exit_proceeds,
            holding_period_days=holding_period,
            exit_reason=exit_reason
        )
        
        # Add proceeds to cash
        self.cash += exit_proceeds
        
        # Remove position
        del self.positions[ticker]
        
        # Record trade
        self.closed_trades.append(trade)
        
        logger.info(f"Closed position: {ticker} - P&L: ${pnl:.2f} ({pnl_percent:.2f}%) - Reason: {exit_reason}")
        
        return trade
    
    def check_drawdown_limits(
        self,
        max_daily_drawdown: Optional[float] = None,
        max_weekly_drawdown: Optional[float] = None
    ) -> Tuple[bool, str]:
        """
        Check if portfolio has exceeded drawdown limits
        
        Returns:
            (limit_exceeded, reason)
        """
        if max_daily_drawdown is not None:
            daily_dd = ((self.peak_value_today - self.portfolio_value) / self.peak_value_today) * 100
            if daily_dd > max_daily_drawdown:
                self.trading_halted = True
                return True, f"Daily drawdown limit exceeded: {daily_dd:.2f}% > {max_daily_drawdown}%"
        
        if max_weekly_drawdown is not None:
            weekly_dd = ((self.peak_value_this_week - self.portfolio_value) / self.peak_value_this_week) * 100
            if weekly_dd > max_weekly_drawdown:
                self.trading_halted = True
                return True, f"Weekly drawdown limit exceeded: {weekly_dd:.2f}% > {max_weekly_drawdown}%"
        
        return False, "OK"
    
    def reset_daily_peak(self):
        """Reset daily peak (call at start of new day)"""
        self.peak_value_today = self.portfolio_value
    
    def reset_weekly_peak(self):
        """Reset weekly peak (call at start of new week)"""
        self.peak_value_this_week = self.portfolio_value
    
    def _calculate_sector_exposure(self, sector: str) -> float:
        """Calculate total exposure to a sector"""
        # This would require sector data for each position
        # For now, returning 0
        return 0.0
    
    def get_position_summary(self) -> Dict:
        """Get summary of current positions"""
        return {
            'num_positions': len(self.positions),
            'total_value': self.total_position_value,
            'unrealized_pnl': self.total_unrealized_pnl,
            'positions': [
                {
                    'ticker': pos.ticker,
                    'shares': pos.shares,
                    'entry_price': pos.entry_price,
                    'current_price': pos.current_price,
                    'value': pos.current_value,
                    'pnl': pos.unrealized_pnl,
                    'pnl_percent': pos.unrealized_pnl_percent,
                    'days_held': pos.days_held
                }
                for pos in self.positions.values()
            ]
        }
    
    def get_trade_summary(self) -> Dict:
        """Get summary of closed trades"""
        if not self.closed_trades:
            return {
                'num_trades': 0,
                'total_pnl': 0.0,
                'win_rate': 0.0,
                'avg_pnl': 0.0
            }
        
        winning_trades = [t for t in self.closed_trades if t.pnl > 0]
        losing_trades = [t for t in self.closed_trades if t.pnl < 0]
        
        return {
            'num_trades': len(self.closed_trades),
            'num_winning': len(winning_trades),
            'num_losing': len(losing_trades),
            'total_pnl': sum(t.pnl for t in self.closed_trades),
            'win_rate': (len(winning_trades) / len(self.closed_trades)) * 100,
            'avg_win': sum(t.pnl for t in winning_trades) / len(winning_trades) if winning_trades else 0,
            'avg_loss': sum(t.pnl for t in losing_trades) / len(losing_trades) if losing_trades else 0,
            'avg_holding_period': sum(t.holding_period_days for t in self.closed_trades) / len(self.closed_trades)
        }

