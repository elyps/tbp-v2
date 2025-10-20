from __future__ import annotations

import numpy as np
import pandas as pd


def sharpe(returns: pd.Series, rf: float = 0.0, periods_per_year: int = 252) -> float:
    """Calculate annualized Sharpe ratio.
    
    Args:
        returns: Series of returns
        rf: Risk-free rate (annualized)
        periods_per_year: Number of periods per year (252 for daily, 252*6.5 for hourly)
        
    Returns:
        Annualized Sharpe ratio
    """
    if returns.std() == 0:
        return 0.0
    excess = returns.mean() - rf / periods_per_year
    return np.sqrt(periods_per_year) * excess / returns.std()


def max_drawdown(equity: pd.Series) -> float:
    """Calculate maximum drawdown.
    
    Args:
        equity: Equity curve
        
    Returns:
        Maximum drawdown (negative value, e.g., -0.15 for 15% drawdown)
    """
    roll_max = equity.cummax()
    dd = equity / roll_max - 1.0
    return dd.min()


def calmar(returns: pd.Series, equity: pd.Series, periods_per_year: int = 252) -> float:
    """Calculate Calmar ratio (CAGR / abs(MaxDD)).
    
    Args:
        returns: Series of returns
        equity: Equity curve
        periods_per_year: Number of periods per year
        
    Returns:
        Calmar ratio
    """
    if len(equity) < 2:
        return 0.0
    cagr = (equity.iloc[-1] / equity.iloc[0]) ** (periods_per_year / len(equity)) - 1
    mdd = abs(max_drawdown(equity))
    if mdd == 0:
        return 0.0
    return cagr / mdd


def profit_factor(returns: pd.Series) -> float:
    """Calculate profit factor (sum of gains / abs(sum of losses)).
    
    Args:
        returns: Series of returns
        
    Returns:
        Profit factor
    """
    gains = returns[returns > 0].sum()
    losses = abs(returns[returns < 0].sum())
    if losses == 0:
        return float('inf') if gains > 0 else 0.0
    return gains / losses


def turnover(positions: pd.Series) -> float:
    """Calculate average daily turnover.
    
    Args:
        positions: Series of position sizes (as fraction of equity)
        
    Returns:
        Average daily turnover
    """
    return positions.diff().abs().mean()


def win_rate(returns: pd.Series) -> float:
    """Calculate win rate (fraction of positive returns).
    
    Args:
        returns: Series of returns
        
    Returns:
        Win rate (0-1)
    """
    trades = returns[returns != 0]
    if len(trades) == 0:
        return 0.0
    return (trades > 0).sum() / len(trades)


def compute_metrics(equity: pd.Series, returns: pd.Series, positions: pd.Series) -> dict:
    """Compute all standard metrics.
    
    Args:
        equity: Equity curve
        returns: Returns series
        positions: Position sizes over time
        
    Returns:
        Dictionary of metrics
    """
    return {
        'sharpe': sharpe(returns),
        'calmar': calmar(returns, equity),
        'max_drawdown': max_drawdown(equity),
        'profit_factor': profit_factor(returns),
        'turnover': turnover(positions),
        'win_rate': win_rate(returns),
        'total_return': (equity.iloc[-1] / equity.iloc[0] - 1) if len(equity) > 0 else 0.0,
    }
