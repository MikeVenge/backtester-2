"""
Performance Metrics Module
Calculates portfolio performance metrics and generates reports
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class PerformanceAnalyzer:
    """Analyzes backtest performance and generates metrics"""
    
    def __init__(self, risk_free_rate: float = 0.02):
        """
        Initialize performance analyzer
        
        Args:
            risk_free_rate: Annual risk-free rate for Sharpe/Sortino calculations
        """
        self.risk_free_rate = risk_free_rate
    
    def calculate_all_metrics(
        self,
        equity_curve: List[Tuple[datetime, float]],
        trades: List['Trade'],
        initial_capital: float,
        benchmark_returns: Optional[pd.Series] = None
    ) -> Dict:
        """
        Calculate all performance metrics
        
        Args:
            equity_curve: List of (timestamp, portfolio_value) tuples
            trades: List of Trade objects
            initial_capital: Starting capital
            benchmark_returns: Optional benchmark returns for comparison
        
        Returns:
            Dictionary with all metrics
        """
        # Convert equity curve to DataFrame
        equity_df = pd.DataFrame(equity_curve, columns=['timestamp', 'value'])
        equity_df = equity_df.set_index('timestamp')
        
        # Calculate returns
        equity_df['returns'] = equity_df['value'].pct_change()
        
        # Basic metrics
        basic_metrics = self.calculate_basic_metrics(equity_df, initial_capital)
        
        # Ratio metrics
        ratio_metrics = self.calculate_ratio_metrics(equity_df)
        
        # Trade statistics
        trade_stats = self.calculate_trade_statistics(trades)
        
        # Benchmark comparison (if provided)
        benchmark_metrics = {}
        if benchmark_returns is not None:
            benchmark_metrics = self.calculate_benchmark_metrics(equity_df['returns'], benchmark_returns)
        
        return {
            'basic_metrics': basic_metrics,
            'ratio_metrics': ratio_metrics,
            'trade_stats': trade_stats,
            'benchmark_metrics': benchmark_metrics
        }
    
    def calculate_basic_metrics(self, equity_df: pd.DataFrame, initial_capital: float) -> Dict:
        """Calculate basic performance metrics"""
        final_value = equity_df['value'].iloc[-1]
        
        # Total return
        total_return = ((final_value - initial_capital) / initial_capital) * 100
        
        # CAGR
        days = (equity_df.index[-1] - equity_df.index[0]).days
        years = days / 365.25
        if years > 0:
            cagr = (((final_value / initial_capital) ** (1 / years)) - 1) * 100
        else:
            cagr = 0.0
        
        # Max drawdown
        max_dd, max_dd_duration = self.calculate_max_drawdown(equity_df['value'])
        
        # Volatility (annualized)
        volatility = equity_df['returns'].std() * np.sqrt(252) * 100
        
        return {
            'total_return': round(total_return, 2),
            'cagr': round(cagr, 2),
            'max_drawdown': round(max_dd, 2),
            'max_drawdown_duration_days': max_dd_duration,
            'volatility': round(volatility, 2),
            'initial_capital': initial_capital,
            'final_value': round(final_value, 2),
            'profit_loss': round(final_value - initial_capital, 2)
        }
    
    def calculate_max_drawdown(self, equity_series: pd.Series) -> Tuple[float, int]:
        """
        Calculate maximum drawdown and its duration
        
        Returns:
            (max_drawdown_percent, duration_in_days)
        """
        cummax = equity_series.cummax()
        drawdown = (equity_series - cummax) / cummax * 100
        
        max_dd = drawdown.min()
        
        # Calculate drawdown duration
        is_drawdown = drawdown < 0
        drawdown_periods = is_drawdown.astype(int).groupby((is_drawdown != is_drawdown.shift()).cumsum()).sum()
        max_dd_duration = drawdown_periods.max() if len(drawdown_periods) > 0 else 0
        
        return abs(max_dd), max_dd_duration
    
    def calculate_ratio_metrics(self, equity_df: pd.DataFrame) -> Dict:
        """Calculate ratio-based performance metrics"""
        returns = equity_df['returns'].dropna()
        
        if len(returns) == 0:
            return {
                'sharpe_ratio': 0.0,
                'sortino_ratio': 0.0,
                'calmar_ratio': 0.0
            }
        
        # Sharpe Ratio
        excess_returns = returns - (self.risk_free_rate / 252)  # Daily risk-free rate
        if returns.std() != 0:
            sharpe_ratio = (excess_returns.mean() / returns.std()) * np.sqrt(252)
        else:
            sharpe_ratio = 0.0
        
        # Sortino Ratio (uses downside deviation)
        downside_returns = returns[returns < 0]
        if len(downside_returns) > 0 and downside_returns.std() != 0:
            sortino_ratio = (excess_returns.mean() / downside_returns.std()) * np.sqrt(252)
        else:
            sortino_ratio = 0.0
        
        # Calmar Ratio (CAGR / Max Drawdown)
        days = (equity_df.index[-1] - equity_df.index[0]).days
        years = days / 365.25
        if years > 0:
            final_value = equity_df['value'].iloc[-1]
            initial_value = equity_df['value'].iloc[0]
            cagr = ((final_value / initial_value) ** (1 / years)) - 1
            
            max_dd, _ = self.calculate_max_drawdown(equity_df['value'])
            if max_dd != 0:
                calmar_ratio = (cagr * 100) / max_dd
            else:
                calmar_ratio = 0.0
        else:
            calmar_ratio = 0.0
        
        return {
            'sharpe_ratio': round(sharpe_ratio, 2),
            'sortino_ratio': round(sortino_ratio, 2),
            'calmar_ratio': round(calmar_ratio, 2)
        }
    
    def calculate_trade_statistics(self, trades: List['Trade']) -> Dict:
        """Calculate trade-level statistics"""
        if not trades:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0.0,
                'average_win': 0.0,
                'average_loss': 0.0,
                'avg_win_loss_ratio': 0.0,
                'profit_factor': 0.0,
                'average_holding_period': 0.0,
                'largest_win': 0.0,
                'largest_loss': 0.0
            }
        
        winning_trades = [t for t in trades if t.pnl > 0]
        losing_trades = [t for t in trades if t.pnl < 0]
        
        total_trades = len(trades)
        num_winning = len(winning_trades)
        num_losing = len(losing_trades)
        
        # Win rate
        win_rate = (num_winning / total_trades) * 100 if total_trades > 0 else 0
        
        # Average win/loss
        avg_win = sum(t.pnl for t in winning_trades) / num_winning if num_winning > 0 else 0
        avg_loss = sum(t.pnl for t in losing_trades) / num_losing if num_losing > 0 else 0
        
        # Average win/loss ratio
        avg_win_loss_ratio = abs(avg_win / avg_loss) if avg_loss != 0 else 0
        
        # Profit factor
        gross_profit = sum(t.pnl for t in winning_trades)
        gross_loss = abs(sum(t.pnl for t in losing_trades))
        profit_factor = gross_profit / gross_loss if gross_loss != 0 else 0
        
        # Average holding period
        avg_holding = sum(t.holding_period_days for t in trades) / total_trades
        
        # Largest win/loss
        largest_win = max((t.pnl for t in trades), default=0)
        largest_loss = min((t.pnl for t in trades), default=0)
        
        return {
            'total_trades': total_trades,
            'winning_trades': num_winning,
            'losing_trades': num_losing,
            'win_rate': round(win_rate, 2),
            'average_win': round(avg_win, 2),
            'average_loss': round(avg_loss, 2),
            'avg_win_loss_ratio': round(avg_win_loss_ratio, 2),
            'profit_factor': round(profit_factor, 2),
            'average_holding_period': round(avg_holding, 1),
            'largest_win': round(largest_win, 2),
            'largest_loss': round(largest_loss, 2)
        }
    
    def calculate_benchmark_metrics(
        self,
        portfolio_returns: pd.Series,
        benchmark_returns: pd.Series
    ) -> Dict:
        """Calculate metrics vs benchmark"""
        # Align returns
        aligned_returns = pd.DataFrame({
            'portfolio': portfolio_returns,
            'benchmark': benchmark_returns
        }).dropna()
        
        if len(aligned_returns) == 0:
            return {
                'alpha': 0.0,
                'beta': 0.0,
                'tracking_error': 0.0,
                'information_ratio': 0.0
            }
        
        # Beta
        covariance = aligned_returns['portfolio'].cov(aligned_returns['benchmark'])
        benchmark_variance = aligned_returns['benchmark'].var()
        beta = covariance / benchmark_variance if benchmark_variance != 0 else 0
        
        # Alpha (annualized)
        portfolio_return = aligned_returns['portfolio'].mean() * 252
        benchmark_return = aligned_returns['benchmark'].mean() * 252
        alpha = (portfolio_return - (self.risk_free_rate + beta * (benchmark_return - self.risk_free_rate))) * 100
        
        # Tracking error (annualized)
        excess_returns = aligned_returns['portfolio'] - aligned_returns['benchmark']
        tracking_error = excess_returns.std() * np.sqrt(252) * 100
        
        # Information ratio
        if tracking_error != 0:
            information_ratio = (excess_returns.mean() * 252) / (excess_returns.std() * np.sqrt(252))
        else:
            information_ratio = 0.0
        
        return {
            'alpha': round(alpha, 2),
            'beta': round(beta, 2),
            'tracking_error': round(tracking_error, 2),
            'information_ratio': round(information_ratio, 2)
        }
    
    def generate_monthly_returns_table(self, equity_df: pd.DataFrame) -> pd.DataFrame:
        """Generate monthly returns table"""
        equity_df = equity_df.copy()
        equity_df['year'] = equity_df.index.year
        equity_df['month'] = equity_df.index.month
        
        # Calculate monthly returns
        monthly_returns = equity_df.groupby(['year', 'month'])['value'].last().pct_change() * 100
        
        # Pivot to table format
        monthly_table = monthly_returns.reset_index()
        monthly_table.columns = ['Year', 'Month', 'Return']
        
        return monthly_table
    
    def generate_annual_returns_table(self, equity_df: pd.DataFrame) -> pd.DataFrame:
        """Generate annual returns table"""
        equity_df = equity_df.copy()
        equity_df['year'] = equity_df.index.year
        
        # Get first and last value of each year
        annual_start = equity_df.groupby('year')['value'].first()
        annual_end = equity_df.groupby('year')['value'].last()
        
        annual_returns = ((annual_end - annual_start) / annual_start * 100).round(2)
        
        return annual_returns.to_frame('Return')
    
    def generate_drawdown_distribution(self, equity_df: pd.DataFrame) -> pd.DataFrame:
        """Generate distribution of drawdowns"""
        cummax = equity_df['value'].cummax()
        drawdown = (equity_df['value'] - cummax) / cummax * 100
        
        # Categorize drawdowns
        bins = [0, -5, -10, -15, -20, -30, -50, -100]
        labels = ['0-5%', '5-10%', '10-15%', '15-20%', '20-30%', '30-50%', '>50%']
        
        drawdown_negative = drawdown[drawdown < 0].abs()
        
        if len(drawdown_negative) > 0:
            distribution = pd.cut(drawdown_negative, bins=bins, labels=labels).value_counts()
        else:
            distribution = pd.Series(0, index=labels)
        
        return distribution.to_frame('Count')
    
    def export_trade_log(self, trades: List['Trade']) -> pd.DataFrame:
        """Export trade log as DataFrame"""
        if not trades:
            return pd.DataFrame()
        
        trade_data = []
        for trade in trades:
            trade_data.append({
                'Ticker': trade.ticker,
                'Entry Date': trade.entry_date,
                'Entry Price': round(trade.entry_price, 2),
                'Exit Date': trade.exit_date,
                'Exit Price': round(trade.exit_price, 2),
                'Shares': trade.shares,
                'P&L': round(trade.pnl, 2),
                'P&L %': round(trade.pnl_percent, 2),
                'Holding Period': trade.holding_period_days,
                'Exit Reason': trade.exit_reason
            })
        
        return pd.DataFrame(trade_data)

