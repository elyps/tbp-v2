"""Test cost application."""
import pytest

from trader.backtest.costs import apply_costs


def test_costs_reduce_pnl():
    """Test that costs reduce gross PnL."""
    pnl_gross = 100
    pnl_net = apply_costs(pnl_gross, fee_bps=2, slip_bps=6, notional=1000)
    
    # Should be less than gross
    assert pnl_net < pnl_gross


def test_costs_calculation():
    """Test exact cost calculation."""
    pnl_gross = 100
    notional = 1000
    
    # 2 bps fee + 6 bps slip = 8 bps total
    # 1000 * 0.0008 = 0.8
    pnl_net = apply_costs(pnl_gross, fee_bps=2, slip_bps=6, notional=notional)
    
    expected = 100 - 0.8
    assert abs(pnl_net - expected) < 0.001


def test_costs_on_loss():
    """Test that costs increase losses."""
    pnl_gross = -50
    pnl_net = apply_costs(pnl_gross, fee_bps=2, slip_bps=6, notional=1000)
    
    # Loss should be larger (more negative)
    assert pnl_net < pnl_gross


def test_costs_proportional_to_notional():
    """Test that costs scale with notional."""
    cost_small = 100 - apply_costs(100, fee_bps=2, slip_bps=6, notional=1000)
    cost_large = 100 - apply_costs(100, fee_bps=2, slip_bps=6, notional=2000)
    
    # Larger notional should have larger costs
    assert cost_large > cost_small
    assert abs(cost_large - 2 * cost_small) < 0.001
