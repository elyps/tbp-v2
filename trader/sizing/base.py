from typing import Protocol

import pandas as pd


class IPositionSizer(Protocol):
    def size_fraction(self, row: pd.Series, conf: float, atr: float) -> float:
        ...
