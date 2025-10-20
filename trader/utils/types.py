"""Common type definitions for the trading pipeline."""
from __future__ import annotations

from typing import Literal, TypeAlias

# Position side types
Side: TypeAlias = Literal["long", "short", "flat"]
OrderSide: TypeAlias = Literal["buy", "sell"]
OrderType: TypeAlias = Literal["market", "limit", "stop"]

# Model types
ModelType: TypeAlias = Literal["trend_meta", "ml_ensemble", "rl_agent"]
SizerType: TypeAlias = Literal["vol", "rl", "fixed"]
