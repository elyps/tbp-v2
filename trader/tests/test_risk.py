"""Test risk management."""
import pandas as pd
import pytest

from trader.risk.portfolio import PortfolioRiskManager
from trader.risk.rules import RiskParams, compute_stop, compute_trailing_stop


def test_compute_stop_long():
    """Test stop calculation for long position."""
    stop = compute_stop(entry_price=100, atr=2, side="long", k=2.0)
    
    assert stop == 96  # 100 - 2*2


def test_compute_stop_short():
    """Test stop calculation for short position."""
    stop = compute_stop(entry_price=100, atr=2, side="short", k=2.0)
    
    assert stop == 104  # 100 + 2*2


def test_compute_stop_flat():
    """Test stop returns None for flat."""
    stop = compute_stop(entry_price=100, atr=2, side="flat", k=2.0)
    
    assert stop is None


def test_trailing_stop_long():
    """Test trailing stop for long position."""
    stop = compute_trailing_stop(
        current_price=105, best_price=110, atr=2, side="long", k=3.0
    )
    
    assert stop == 104  # 110 - 3*2


def test_trailing_stop_short():
    """Test trailing stop for short position."""
    stop = compute_trailing_stop(
        current_price=95, best_price=90, atr=2, side="short", k=3.0
    )
    
    assert stop == 96  # 90 + 3*2


def test_portfolio_position_cap():
    """Test that portfolio manager caps positions."""
    params = RiskParams(max_pos_per_asset=0.03)
    mgr = PortfolioRiskManager(params)
    
    capped = mgr.check_position_size("AAPL", 0.10, {})
    
    assert capped == 0.03


def test_portfolio_gross_limit():
    """Test gross exposure limit."""
    params = RiskParams(max_gross=0.6)
    mgr = PortfolioRiskManager(params)
    
    current = {"AAPL": 0.3, "MSFT": 0.2}
    
    # Already at 0.5, can add 0.1 more
    allowed = mgr.check_gross_exposure(0.15, current)
    
    assert allowed == 0.1


def test_daily_drawdown_kill_switch():
    """Test that kill-switch triggers on drawdown."""
    params = RiskParams(day_dd_kill=0.08)
    mgr = PortfolioRiskManager(params)
    
    timestamp = pd.Timestamp('2023-01-01 10:00', tz='UTC')
    
    # 10% drawdown should trigger (> 8% threshold)
    triggered = mgr.check_daily_drawdown(9000, 10000, timestamp)
    
    assert triggered is True
    assert mgr.kill_switch_active is True


def test_kill_switch_cooldown():
    """Test that kill-switch respects cooldown period."""
    params = RiskParams(day_dd_kill=0.08)
    mgr = PortfolioRiskManager(params)
    
    timestamp1 = pd.Timestamp('2023-01-01 10:00', tz='UTC')
    
    # Trigger kill-switch
    mgr.check_daily_drawdown(9000, 10000, timestamp1)
    
    # Still in cooldown 2 hours later
    timestamp2 = pd.Timestamp('2023-01-01 12:00', tz='UTC')
    still_active = mgr.check_daily_drawdown(9500, 10000, timestamp2)
    
    assert still_active is True


def test_kill_switch_reset():
    """Test that kill-switch can be reset."""
    params = RiskParams(day_dd_kill=0.08)
    mgr = PortfolioRiskManager(params)
    
    timestamp = pd.Timestamp('2023-01-01 10:00', tz='UTC')
    mgr.check_daily_drawdown(9000, 10000, timestamp)
    
    assert mgr.kill_switch_active is True
    
    mgr.reset_kill_switch()
    
    assert mgr.kill_switch_active is False
    assert mgr.cooldown_until is None
