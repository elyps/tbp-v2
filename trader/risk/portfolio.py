from __future__ import annotations

from typing import Dict

import pandas as pd

from trader.risk.rules import RiskParams


class PortfolioRiskManager:
    """Enforce portfolio-level risk constraints."""
    
    def __init__(self, params: RiskParams) -> None:
        self.params = params
        self.kill_switch_active = False
        self.cooldown_until: pd.Timestamp | None = None
        
    def check_position_size(
        self, symbol: str, target_fraction: float, current_positions: Dict[str, float]
    ) -> float:
        """Enforce max position per asset.
        
        Args:
            symbol: Asset symbol
            target_fraction: Target position size as fraction of equity
            current_positions: Current positions {symbol: fraction}
            
        Returns:
            Capped position fraction
        """
        return min(target_fraction, self.params.max_pos_per_asset)
    
    def check_gross_exposure(
        self, new_fraction: float, current_positions: Dict[str, float]
    ) -> float:
        """Enforce maximum gross exposure limit.
        
        Args:
            new_fraction: New position fraction to add
            current_positions: Current positions {symbol: fraction}
            
        Returns:
            Adjusted position fraction to stay within gross limit
        """
        current_gross = sum(abs(f) for f in current_positions.values())
        remaining = self.params.max_gross - current_gross
        if remaining <= 0:
            return 0.0
        return min(new_fraction, remaining)
    
    def check_daily_drawdown(
        self, current_equity: float, start_of_day_equity: float, timestamp: pd.Timestamp
    ) -> bool:
        """Check if daily drawdown kill-switch should trigger.
        
        Args:
            current_equity: Current portfolio equity
            start_of_day_equity: Equity at start of trading day
            timestamp: Current timestamp
            
        Returns:
            True if kill-switch triggered (should flatten all positions)
        """
        if self.cooldown_until and timestamp < self.cooldown_until:
            return True
            
        dd = (current_equity - start_of_day_equity) / start_of_day_equity
        if dd < -self.params.day_dd_kill:
            self.kill_switch_active = True
            # Set cooldown to end of day + 1 day
            self.cooldown_until = timestamp.normalize() + pd.Timedelta(days=1)
            return True
            
        return False
    
    def reset_kill_switch(self) -> None:
        """Reset kill-switch (typically at start of new day)."""
        self.kill_switch_active = False
        self.cooldown_until = None
