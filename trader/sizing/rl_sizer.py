"""Placeholder for RL-based position sizing (future upgrade)."""
from __future__ import annotations

import pandas as pd


class RLSizer:
    """Reinforcement Learning-based position sizer (PPO/SAC).
    
    This is a placeholder for future implementation.
    Only controls position size, not trade direction.
    """
    
    def __init__(self, target_vol: float = 0.10, cap: float = 0.03) -> None:
        self.target_vol = target_vol
        self.cap = cap
        # TODO: Initialize RL agent (PPO/SAC)
        
    def size_fraction(self, row: pd.Series, conf: float, atr: float) -> float:
        # TODO: Implement RL-based sizing
        # For now, fallback to vol-based sizing
        if atr is None or atr <= 0 or conf <= 0:
            return 0.0
        unit = self.target_vol / atr
        return float(min(self.cap, unit * conf))
