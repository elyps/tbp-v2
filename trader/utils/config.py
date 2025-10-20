from pathlib import Path
from typing import Any, Callable, Dict, Optional

import yaml
from pydantic import BaseModel, Field


class DataConfig(BaseModel):
    symbols: list[str] = Field(default_factory=list)
    bar: str = "1h"
    path: Optional[str] = None
    loader: Optional[str] = None
    start: Optional[str] = None
    end: Optional[str] = None


class BacktestConfig(BaseModel):
    train_days: int = 252
    test_days: int = 63
    step_days: int = 63
    fee_bps: int = 2
    slippage_bps: int = 6


class SignalConfig(BaseModel):
    type: str = "trend_meta"
    p_up: float = 0.55
    p_dn: float = 0.55
    allow_short: bool = False
    params: Dict[str, Any] = Field(default_factory=dict)


class SizingConfig(BaseModel):
    type: str = "vol"
    target_vol: float = 0.1
    cap: float = 0.03
    params: Dict[str, Any] = Field(default_factory=dict)


class RiskConfig(BaseModel):
    max_pos_per_asset: float = 0.03
    max_gross: float = 0.6
    stop_atr_mult: float = 2.0
    trail_atr_mult: float = 3.0
    day_dd_kill: float = 0.08


class LoggingConfig(BaseModel):
    level: str = "INFO"
    seed: int = 42


class Config(BaseModel):
    data: DataConfig
    backtest: BacktestConfig
    signals: SignalConfig
    sizing: SizingConfig
    risk: RiskConfig
    logging: LoggingConfig = Field(default_factory=LoggingConfig)


def load_cfg(path: str | Path) -> Config:
    with Path(path).open("r", encoding="utf-8") as fh:
        doc = yaml.safe_load(fh)
    return Config(**doc)


def build_callable(path: str | None) -> Optional[Callable[..., Any]]:
    if not path:
        return None
    module_path, _, attr = path.rpartition(".")
    if not module_path:
        raise ValueError(f"Invalid callable path: {path}")
    module = __import__(module_path, fromlist=[attr])
    return getattr(module, attr)
