from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional


@dataclass
class RiskParams:
    max_pos_per_asset: float = 0.03
    max_gross: float = 0.6
    stop_atr_mult: float = 2.0
    trail_atr_mult: float = 3.0
    day_dd_kill: float = 0.08


def compute_stop(
    entry_price: float,
    atr: float,
    side: Literal["long", "short", "flat"],
    k: float = 2.0,
) -> Optional[float]:
    """Compute stop-loss level based on entry price, ATR, and position side.
    
    Args:
        entry_price: Entry price of the position
        atr: Average True Range at entry
        side: Position side ("long", "short", or "flat")
        k: ATR multiplier for stop distance
        
    Returns:
        Stop price level, or None if side is "flat"
    """
    if side == "long":
        return entry_price - k * atr
    if side == "short":
        return entry_price + k * atr
    return None


def compute_trailing_stop(
    current_price: float,
    best_price: float,
    atr: float,
    side: Literal["long", "short"],
    k: float = 3.0,
) -> Optional[float]:
    """Compute trailing stop level.
    
    Args:
        current_price: Current market price
        best_price: Best price achieved since entry (highest for long, lowest for short)
        atr: Current Average True Range
        side: Position side
        k: ATR multiplier for trailing distance
        
    Returns:
        Trailing stop price level
    """
    if side == "long":
        return best_price - k * atr
    if side == "short":
        return best_price + k * atr
    return None
