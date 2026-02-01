"""
Performance metrics for backtest reports.

Calculates Sharpe ratio, Sortino ratio, drawdown, win rate, and more.
"""

import math
from typing import List, Dict, Any
from dataclasses import dataclass
from datetime import datetime

from ..strategy.position import ClosedPosition


@dataclass
class BacktestMetrics:
    """Complete backtest performance metrics."""
    
    # Summary
    net_profit: float = 0
    net_profit_pct: float = 0
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0
    profit_factor: float = 0
    
    # Returns
    total_return: float = 0
    annualized_return: float = 0
    monthly_return: float = 0
    
    # Risk metrics
    max_drawdown: float = 0
    max_drawdown_pct: float = 0
    max_drawdown_duration_days: int = 0
    volatility: float = 0
    sharpe_ratio: float = 0
    sortino_ratio: float = 0
    calmar_ratio: float = 0
    value_at_risk: float = 0  # 95% VaR
    
    # Trade statistics
    avg_win: float = 0
    avg_loss: float = 0
    largest_win: float = 0
    largest_loss: float = 0
    avg_trade: float = 0
    avg_bars_in_trade: float = 0
    expectancy: float = 0
    
    # Streaks
    max_consecutive_wins: int = 0
    max_consecutive_losses: int = 0
    recovery_factor: float = 0
    
    # Performance breakdown
    gross_profit: float = 0
    gross_loss: float = 0
    
    # Alpha/Beta (vs benchmark)
    alpha: float = 0
    beta: float = 0


def calculate_metrics(
    trades: List[ClosedPosition],
    equity_curve: List[float],
    initial_capital: float,
    start_date: datetime,
    end_date: datetime,
    risk_free_rate: float = 0.02,  # 2% annual
) -> BacktestMetrics:
    """
    Calculate all performance metrics.
    
    Args:
        trades: List of closed trades
        equity_curve: Time series of equity values
        initial_capital: Starting capital
        start_date: Backtest start date
        end_date: Backtest end date
        risk_free_rate: Annual risk-free rate
        
    Returns:
        BacktestMetrics with all calculated values
    """
    metrics = BacktestMetrics()
    
    if not trades or not equity_curve:
        return metrics
    
    # Basic counts
    metrics.total_trades = len(trades)
    metrics.winning_trades = sum(1 for t in trades if t.pnl > 0)
    metrics.losing_trades = sum(1 for t in trades if t.pnl < 0)
    
    # Win rate
    if metrics.total_trades > 0:
        metrics.win_rate = (metrics.winning_trades / metrics.total_trades) * 100
    
    # Profit/Loss calculations
    winning_pnls = [t.pnl for t in trades if t.pnl > 0]
    losing_pnls = [t.pnl for t in trades if t.pnl < 0]
    
    metrics.gross_profit = sum(winning_pnls)
    metrics.gross_loss = abs(sum(losing_pnls))
    metrics.net_profit = metrics.gross_profit - metrics.gross_loss
    metrics.net_profit_pct = (metrics.net_profit / initial_capital) * 100
    
    # Profit factor
    if metrics.gross_loss > 0:
        metrics.profit_factor = metrics.gross_profit / metrics.gross_loss
    else:
        if metrics.gross_profit > 0:
            metrics.profit_factor = 100.0 # Capped for display/JSON safety
        else:
            metrics.profit_factor = 0.0
    
    # Average win/loss
    if winning_pnls:
        metrics.avg_win = sum(winning_pnls) / len(winning_pnls)
        metrics.largest_win = max(winning_pnls)
    
    if losing_pnls:
        metrics.avg_loss = sum(losing_pnls) / len(losing_pnls)  # Negative
        metrics.largest_loss = min(losing_pnls)  # Most negative
    
    # Average trade
    if trades:
        metrics.avg_trade = metrics.net_profit / len(trades)
        
        # Average bars in trade (using duration)
        avg_duration_hours = sum(t.duration_seconds for t in trades) / len(trades) / 3600
        metrics.avg_bars_in_trade = avg_duration_hours / 24  # Days
    
    # Expectancy
    if metrics.win_rate > 0 and metrics.avg_win and metrics.avg_loss:
        win_prob = metrics.win_rate / 100
        loss_prob = 1 - win_prob
        metrics.expectancy = (win_prob * metrics.avg_win) + (loss_prob * metrics.avg_loss)
    
    # Returns
    final_equity = equity_curve[-1] if equity_curve else initial_capital
    metrics.total_return = ((final_equity - initial_capital) / initial_capital) * 100
    
    # Calculate period in years
    days = (end_date - start_date).days
    years = max(days / 365.25, 1/365)  # At least 1 day
    
    if metrics.total_return > -100:
        metrics.annualized_return = ((1 + metrics.total_return/100) ** (1/years) - 1) * 100
    metrics.monthly_return = metrics.annualized_return / 12
    
    # Drawdown analysis
    peak = initial_capital
    max_dd = 0
    max_dd_pct = 0
    dd_start = 0
    max_dd_duration = 0
    
    for i, equity in enumerate(equity_curve):
        if equity > peak:
            # New peak, reset drawdown tracking
            dd_duration = i - dd_start
            if dd_duration > max_dd_duration:
                max_dd_duration = dd_duration
            peak = equity
            dd_start = i
        else:
            drawdown = peak - equity
            drawdown_pct = (drawdown / peak) * 100
            if drawdown > max_dd:
                max_dd = drawdown
            if drawdown_pct > max_dd_pct:
                max_dd_pct = drawdown_pct
    
    metrics.max_drawdown = max_dd
    metrics.max_drawdown_pct = max_dd_pct
    metrics.max_drawdown_duration_days = max_dd_duration
    
    # Volatility (annualized std dev of returns)
    if len(equity_curve) > 1:
        returns = []
        for i in range(1, len(equity_curve)):
            denom = equity_curve[i-1]
            if abs(denom) > 1e-9:
                daily_return = (equity_curve[i] - denom) / denom
                returns.append(daily_return)
            else:
                returns.append(0.0)
        
        if returns:
            mean_return = sum(returns) / len(returns)
            variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
            daily_std = math.sqrt(variance)
            metrics.volatility = daily_std * math.sqrt(252) * 100  # Annualized
    
    # Sharpe Ratio
    if metrics.volatility > 0:
        excess_return = metrics.annualized_return - (risk_free_rate * 100)
        metrics.sharpe_ratio = excess_return / metrics.volatility
    
    # Sortino Ratio (uses downside deviation)
    if len(equity_curve) > 1:
        returns = []
        for i in range(1, len(equity_curve)):
            denom = equity_curve[i-1]
            if abs(denom) > 1e-9:
                returns.append((equity_curve[i] - denom) / denom)
            else:
                returns.append(0.0)
        negative_returns = [r for r in returns if r < 0]
        
        if negative_returns:
            downside_variance = sum(r ** 2 for r in negative_returns) / len(returns)
            downside_std = math.sqrt(downside_variance) * math.sqrt(252) * 100
            if downside_std > 0:
                excess_return = metrics.annualized_return - (risk_free_rate * 100)
                metrics.sortino_ratio = excess_return / downside_std
    
    # Calmar Ratio
    if metrics.max_drawdown_pct > 0:
        metrics.calmar_ratio = metrics.annualized_return / metrics.max_drawdown_pct
    
    # Value at Risk (95%)
    if len(equity_curve) > 1:
        returns = []
        for i in range(1, len(equity_curve)):
            denom = equity_curve[i-1]
            if abs(denom) > 1e-9:
                returns.append((equity_curve[i] - denom) / denom)
            else:
                returns.append(0.0)
        if returns:
            sorted_returns = sorted(returns)
            var_index = int(len(sorted_returns) * 0.05)
            metrics.value_at_risk = sorted_returns[var_index] * 100
    
    # Recovery Factor
    if metrics.max_drawdown > 0:
        metrics.recovery_factor = metrics.net_profit / metrics.max_drawdown
    
    # Consecutive wins/losses
    max_wins = 0
    max_losses = 0
    current_wins = 0
    current_losses = 0
    
    for trade in trades:
        if trade.pnl > 0:
            current_wins += 1
            current_losses = 0
            max_wins = max(max_wins, current_wins)
        elif trade.pnl < 0:
            current_losses += 1
            current_wins = 0
            max_losses = max(max_losses, current_losses)
        else:
            current_wins = 0
            current_losses = 0
    
    metrics.max_consecutive_wins = max_wins
    metrics.max_consecutive_losses = max_losses
    
    return metrics


def calculate_monthly_returns(
    equity_curve: List[float],
    dates: List[datetime],
) -> Dict[str, float]:
    """
    Calculate monthly returns.
    
    Returns:
        Dict mapping "YYYY-MM" to return percentage
    """
    if len(equity_curve) != len(dates):
        return {}
    
    monthly = {}
    current_month = None
    month_start_equity = None
    
    for i, (equity, date) in enumerate(zip(equity_curve, dates)):
        month_key = date.strftime("%Y-%m")
        
        if month_key != current_month:
            # New month
            if current_month and month_start_equity:
                # Calculate previous month's return
                prev_equity = equity_curve[i-1] if i > 0 else month_start_equity
                if abs(month_start_equity) > 1e-9:
                    monthly[current_month] = ((prev_equity - month_start_equity) / month_start_equity) * 100
                else:
                    monthly[current_month] = 0.0
            
            current_month = month_key
            month_start_equity = equity
    
    # Final month
    if current_month and month_start_equity:
        if abs(month_start_equity) > 1e-9:
            monthly[current_month] = ((equity_curve[-1] - month_start_equity) / month_start_equity) * 100
        else:
            monthly[current_month] = 0.0
    
    return monthly
