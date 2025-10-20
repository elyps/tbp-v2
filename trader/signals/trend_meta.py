from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pandas as pd
from xgboost import XGBClassifier

from trader.data.features import trend_gate


@dataclass
class TrendMetaConfig:
    p_up: float = 0.55
    p_dn: float = 0.55
    allow_short: bool = False
    xgb_kwargs: Optional[dict] = None


class TrendMeta:
    def __init__(
        self,
        p_up: float = 0.55,
        p_dn: float = 0.55,
        allow_short: bool = False,
        **xgb_kwargs,
    ) -> None:
        self.p_up = p_up
        self.p_dn = p_dn
        self.allow_short = allow_short
        params = {
            "n_estimators": 200,  # Reduced from 400 for XGBoost
            "max_depth": 6,  # Equivalent to LGBM -1 (unlimited, but cap at 6 for safety)
            "learning_rate": 0.05,  # Slightly higher than LGBM
            "subsample": 0.8,
            "colsample_bytree": 0.8,
            "random_state": 42,
            "verbosity": 0,  # Suppress XGBoost warnings
        }
        params.update(xgb_kwargs)
        self.clf = XGBClassifier(**params)

    def fit(self, X: pd.DataFrame, y: pd.Series) -> None:
        feats = [c for c in X.columns if c != "y"]
        self._feat_cols = feats
        X_train = X[feats]
        self.clf.fit(X_train, y)

    def predict_conf(self, X: pd.DataFrame) -> pd.Series:
        if not self._feat_cols:
            raise RuntimeError("Model not fit")
        probs = self.clf.predict_proba(X[self._feat_cols])[:, 1]
        return pd.Series(probs, index=X.index).clip(0.0, 1.0)

    def predict_side(self, X: pd.DataFrame) -> pd.Series:
        gate = trend_gate(X)
        conf = self.predict_conf(X)
        side = pd.Series("flat", index=X.index, dtype="object")
        side.loc[gate & (conf >= self.p_up)] = "long"
        if self.allow_short:
            side.loc[(~gate) & ((1 - conf) >= self.p_dn)] = "short"
        return side
