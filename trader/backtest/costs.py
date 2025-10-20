def apply_costs(
    pnl_gross: float, fee_bps: int = 2, slip_bps: int = 6, notional: float = 1.0
) -> float:
    """Apply trading costs (fees + slippage) to gross PnL.
    
    Args:
        pnl_gross: Gross profit/loss before costs
        fee_bps: Trading fee in basis points (1 bps = 0.01%)
        slip_bps: Slippage in basis points
        notional: Notional trade size
        
    Returns:
        Net PnL after costs
    """
    fees = abs(notional) * (fee_bps / 1e4)
    slip = abs(notional) * (slip_bps / 1e4)
    return pnl_gross - fees - slip
