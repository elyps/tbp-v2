from __future__ import annotations

import pandas as pd


class VolSizer:
    def __init__(self, target_vol: float = 0.10, cap: float = 0.03) -> None:
        self.target_vol = target_vol
        self.cap = cap

    def size_fraction(self, row: pd.Series, conf: float, atr: float) -> float:
        if atr is None or atr <= 0 or conf <= 0:
            return 0.0
        unit = self.target_vol / atr
        return float(min(self.cap, unit * conf))
