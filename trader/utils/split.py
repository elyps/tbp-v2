from __future__ import annotations

from typing import Iterator

import pandas as pd


def rolling_splits(
    idx: pd.DatetimeIndex,
    train: int = 252,
    test: int = 63,
    step: int = 63,
) -> Iterator[tuple[pd.DatetimeIndex, pd.DatetimeIndex]]:
    """Generate rolling train/test splits for walk-forward validation.
    
    Args:
        idx: DatetimeIndex to split
        train: Number of periods for training
        test: Number of periods for testing
        step: Step size between splits
        
    Yields:
        Tuples of (train_index, test_index)
    """
    i = 0
    while i + train + test <= len(idx):
        train_idx = idx[i : i + train]
        test_idx = idx[i + train : i + train + test]
        yield train_idx, test_idx
        i += step
