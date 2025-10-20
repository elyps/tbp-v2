from typing import Protocol

import pandas as pd


class ISignalModel(Protocol):
    def fit(self, X: pd.DataFrame, y: pd.Series) -> None:
        ...

    def predict_side(self, X: pd.DataFrame) -> pd.Series:
        ...

    def predict_conf(self, X: pd.DataFrame) -> pd.Series:
        ...
