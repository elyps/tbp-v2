"""Test performance metrics."""
import numpy as np
import pandas as pd
import pytest

from trader.backtest.metrics import (
    calmar,
    max_drawdown,
    profit_factor,
    sharpe,
    turnover,
    win_rate,
)


def test_sharpe_positive_returns():
    """Test Sharpe ratio on positive returns."""
    returns = pd.Series([0.01, 0.02, 0.01, 0.015, 0.01] * 50)
    
    sr = sharpe(returns, rf=0.0)
    
    assert sr > 0


def test_sharpe_zero_volatility():
    """Test Sharpe handles zero volatility."""
    returns = pd.Series([0.01] * 100)
    
    sr = sharpe(returns)
    
    assert sr == 0.0


def test_max_drawdown_range():
    """Test that max drawdown is negative."""
    equity = pd.Series([100, 110, 105, 95, 100, 120])
    
    mdd = max_drawdown(equity)
    
    assert mdd < 0  # Should be negative


def test_max_drawdown_no_drawdown():
    """Test max drawdown on always-increasing equity."""
    equity = pd.Series([100, 110, 120, 130, 140])
    
    mdd = max_drawdown(equity)
    
    assert mdd == 0.0


def test_profit_factor():
    """Test profit factor calculation."""
    returns = pd.Series([0.1, -0.05, 0.08, -0.03, 0.12])
    
    pf = profit_factor(returns)
    
    # Sum of gains / abs(sum of losses) = 0.3 / 0.08 = 3.75
    assert abs(pf - 3.75) < 0.01


def test_profit_factor_no_losses():
    """Test profit factor with no losses."""
    returns = pd.Series([0.1, 0.05, 0.08])
    
    pf = profit_factor(returns)
    
    assert pf == float('inf')


def test_profit_factor_no_gains():
    """Test profit factor with no gains."""
    returns = pd.Series([-0.1, -0.05, -0.08])
    
    pf = profit_factor(returns)
    
    assert pf == 0.0


def test_win_rate():
    """Test win rate calculation."""
    returns = pd.Series([0.1, -0.05, 0.08, -0.03, 0.12, 0.0])
    
    wr = win_rate(returns)
    
    # 3 wins out of 5 non-zero trades = 60%
    assert abs(wr - 0.6) < 0.01


def test_turnover():
    """Test turnover calculation."""
    positions = pd.Series([0.0, 0.3, 0.3, 0.0, 0.2])
    
    to = turnover(positions)
    
    # Changes: 0.3, 0.0, 0.3, 0.2 -> avg = 0.2
    assert to > 0


def test_calmar_ratio():
    """Test Calmar ratio calculation."""
    equity = pd.Series(np.linspace(100, 120, 252))  # Steady growth
    returns = equity.pct_change().fillna(0)
    
    cr = calmar(returns, equity)
    
    assert cr > 0
