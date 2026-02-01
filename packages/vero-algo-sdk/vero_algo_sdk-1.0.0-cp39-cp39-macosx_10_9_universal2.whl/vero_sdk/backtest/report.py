"""
Performance report for backtest results.

Generates text and data reports matching the provided screenshot format.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any
from datetime import datetime

from .metrics import BacktestMetrics, calculate_monthly_returns
from ..strategy.position import ClosedPosition


@dataclass
class TradeRecord:
    """Trade record for report display."""
    number: int
    type: str  # "LONG" or "SHORT"
    entry_price: float
    exit_price: float
    pnl: float
    pnl_pct: float
    duration: str
    date: str


@dataclass
class PerformanceReport:
    """
    Complete performance report with all metrics and trade history.
    
    Matches the format shown in the provided screenshots.
    """
    
    # Summary
    strategy_name: str = ""
    backtest_period: str = ""
    
    # Core metrics
    metrics: BacktestMetrics = field(default_factory=BacktestMetrics)
    
    # Time series data
    # Time series data ({time: unixtimems, value: float})
    equity_curve: List[float] = field(default_factory=list)
    equity_dates: List[datetime] = field(default_factory=list)
    
    # Monthly returns
    monthly_returns: Dict[str, float] = field(default_factory=dict)
    
    # Trade history
    trades: List[TradeRecord] = field(default_factory=list)
    
    def print_report(self) -> None:
        """Print formatted report to console."""
        print("\n" + "=" * 80)
        print(f"STRATEGY PERFORMANCE REPORT")
        print(f"{self.strategy_name}")
        print(f"Backtest Period: {self.backtest_period}")
        print("=" * 80)
        
        # Summary section
        print("\n┌─────────────────────────────────────────────────────────────────────────────┐")
        print("│                              SUMMARY                                        │")
        print("├─────────────────────────────────────────────────────────────────────────────┤")
        m = self.metrics
        
        pct_color = "\033[32m" if m.net_profit >= 0 else "\033[31m"
        reset = "\033[0m"
        
        print(f"│  NET PROFIT:     {pct_color}{m.net_profit:>12,.2f}{reset}  │  WIN RATE:       {m.win_rate:>8.1f}%       │")
        print(f"│  TOTAL TRADES:   {m.total_trades:>12}  │  PROFIT FACTOR:  {m.profit_factor:>8.2f}        │")
        print(f"│  WINNING:        {m.winning_trades:>12}  │  MAX DRAWDOWN:   {m.max_drawdown_pct:>7.2f}%        │")
        print(f"│  LOSING:         {m.losing_trades:>12}  │  SHARPE RATIO:   {m.sharpe_ratio:>8.2f}        │")
        print("└─────────────────────────────────────────────────────────────────────────────┘")
        
        # Performance section
        print("\n┌─────────────────────────────────────────────────────────────────────────────┐")
        print("│  PERFORMANCE             │  TRADE STATISTICS        │  RISK METRICS        │")
        print("├──────────────────────────┼──────────────────────────┼──────────────────────┤")
        print(f"│  Total Return:  {m.total_return:>7.2f}% │  Avg Win:     {m.avg_win:>10.2f} │  Sharpe:      {m.sharpe_ratio:>5.2f} │")
        print(f"│  Annual Return: {m.annualized_return:>7.2f}% │  Avg Loss:    {m.avg_loss:>10.2f} │  Sortino:     {m.sortino_ratio:>5.2f} │")
        print(f"│  Monthly Return:{m.monthly_return:>7.2f}% │  Largest Win: {m.largest_win:>10.2f} │  Calmar:      {m.calmar_ratio:>5.2f} │")
        print(f"│  Volatility:    {m.volatility:>7.2f}% │  Largest Loss:{m.largest_loss:>10.2f} │  VaR (95%):  {m.value_at_risk:>5.2f}% │")
        print(f"│  Alpha:         {m.alpha:>7.2f}  │  Avg Trade:   {m.avg_trade:>10.2f} │  Recovery:    {m.recovery_factor:>5.2f} │")
        print(f"│  Beta:          {m.beta:>7.2f}  │  Expectancy:  {m.expectancy:>10.2f} │  Max DD Days:{m.max_drawdown_duration_days:>6} │")
        print("└──────────────────────────┴──────────────────────────┴──────────────────────┘")
        
        # Streaks
        print(f"\n│  STREAKS: Max Consecutive Wins: {m.max_consecutive_wins}  │  Max Consecutive Losses: {m.max_consecutive_losses}")
        print(f"│  Gross Profit: {m.gross_profit:,.2f}  │  Gross Loss: {m.gross_loss:,.2f}")
        
        # Monthly returns
        if self.monthly_returns:
            print("\n┌─────────────────────────────────────────────────────────────────────────────┐")
            print("│                           MONTHLY RETURNS                                    │")
            print("├─────────────────────────────────────────────────────────────────────────────┤")
            
            months_display = []
            for month, ret in sorted(self.monthly_returns.items()):
                color = "\033[32m" if ret >= 0 else "\033[31m"
                months_display.append(f"{month[-2:]}: {color}{ret:>+5.1f}%{reset}")
            
            # Display in rows of 6
            for i in range(0, len(months_display), 6):
                row = months_display[i:i+6]
                print("│  " + "  │  ".join(row))
            
            print("└─────────────────────────────────────────────────────────────────────────────┘")
        
        # Recent trades
        if self.trades:
            print("\n┌─────────────────────────────────────────────────────────────────────────────┐")
            print("│                            RECENT TRADES                                     │")
            print("├────┬─────────┬──────────┬──────────┬──────────┬──────────┬─────────┬────────┤")
            print("│  # │  Type   │   Entry  │    Exit  │    P&L   │     %    │Duration │  Date  │")
            print("├────┼─────────┼──────────┼──────────┼──────────┼──────────┼─────────┼────────┤")
            
            for trade in self.trades[-10:]:  # Last 10 trades
                pnl_color = "\033[32m" if trade.pnl >= 0 else "\033[31m"
                type_symbol = "↗" if trade.type == "LONG" else "↘"
                print(f"│{trade.number:>3} │ {type_symbol} {trade.type:<5} │ {trade.entry_price:>8.2f} │ "
                      f"{trade.exit_price:>8.2f} │ {pnl_color}{trade.pnl:>+8.2f}{reset} │ "
                      f"{pnl_color}{trade.pnl_pct:>+7.2f}%{reset} │ {trade.duration:>7} │ {trade.date:>6} │")
            
            print("└────┴─────────┴──────────┴──────────┴──────────┴──────────┴─────────┴────────┘")
        
        print("\n" + "=" * 80)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary for JSON export."""
        return {
            "strategy_name": self.strategy_name,
            "backtest_period": self.backtest_period,
            "metrics": {
                "net_profit": self.metrics.net_profit,
                "net_profit_pct": self.metrics.net_profit_pct,
                "total_trades": self.metrics.total_trades,
                "winning_trades": self.metrics.winning_trades,
                "losing_trades": self.metrics.losing_trades,
                "win_rate": self.metrics.win_rate,
                "profit_factor": self.metrics.profit_factor,
                "total_return": self.metrics.total_return,
                "annualized_return": self.metrics.annualized_return,
                "max_drawdown_pct": self.metrics.max_drawdown_pct,
                "sharpe_ratio": self.metrics.sharpe_ratio,
                "sortino_ratio": self.metrics.sortino_ratio,
                "calmar_ratio": self.metrics.calmar_ratio,
                "avg_win": self.metrics.avg_win,
                "avg_loss": self.metrics.avg_loss,
                "expectancy": self.metrics.expectancy,
            },
            "monthly_returns": self.monthly_returns,
            "equity_curve": [
                {
                    "time": int(date.timestamp() * 1000),
                    "value": value
                }
                for date, value in zip(self.equity_dates, self.equity_curve)
            ],
            "trades": [
                {
                    "number": t.number,
                    "type": t.type,
                    "entry": t.entry_price,
                    "exit": t.exit_price,
                    "pnl": t.pnl,
                    "pnl_pct": t.pnl_pct,
                    "duration": t.duration,
                    "date": t.date,
                }
                for t in self.trades
            ],
        }
    
    def export_csv(self, filepath: str) -> None:
        """Export trades to CSV file."""
        import csv
        
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['#', 'Type', 'Entry', 'Exit', 'P&L', '%', 'Duration', 'Date'])
            
            for trade in self.trades:
                writer.writerow([
                    trade.number,
                    trade.type,
                    trade.entry_price,
                    trade.exit_price,
                    trade.pnl,
                    trade.pnl_pct,
                    trade.duration,
                    trade.date,
                ])
    
    @classmethod
    def from_backtest(
        cls,
        strategy_name: str,
        start_date: datetime,
        end_date: datetime,
        metrics: BacktestMetrics,
        equity_curve: List[float],
        equity_dates: List[datetime],
        closed_positions: List[ClosedPosition],
    ) -> "PerformanceReport":
        """Create report from backtest results."""
        report = cls(
            strategy_name=strategy_name,
            backtest_period=f"{start_date.strftime('%b %d, %Y')} - {end_date.strftime('%b %d, %Y')}",
            metrics=metrics,
            equity_curve=equity_curve,
            equity_dates=equity_dates,
        )
        
        # Calculate monthly returns
        report.monthly_returns = calculate_monthly_returns(equity_curve, equity_dates)
        
        # Convert closed positions to trade records
        for i, pos in enumerate(closed_positions):
            # Format duration
            hours = pos.duration_seconds / 3600
            if hours >= 24:
                duration = f"{int(hours/24)}d {int(hours%24)}h"
            else:
                duration = f"{int(hours)}h"
            
            report.trades.append(TradeRecord(
                number=i + 1,
                type="LONG" if pos.side.value == "LONG" else "SHORT",
                entry_price=pos.entry_price,
                exit_price=pos.exit_price,
                pnl=pos.pnl,
                pnl_pct=pos.pnl_percent,
                duration=duration,
                date=pos.exit_time.strftime("%Y-%m-%d"),
            ))
        
        return report
