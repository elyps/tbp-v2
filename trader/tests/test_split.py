"""Test walk-forward splits."""
import pandas as pd
import pytest

from trader.utils.split import rolling_splits


def test_splits_disjoint():
    """Test that train and test splits are disjoint."""
    idx = pd.date_range('2023-01-01', periods=1000, freq='1h', tz='UTC')
    
    for train_idx, test_idx in rolling_splits(idx, train=252, test=63, step=63):
        # No overlap between train and test
        overlap = set(train_idx) & set(test_idx)
        assert len(overlap) == 0


def test_splits_sequential():
    """Test that test comes after train."""
    idx = pd.date_range('2023-01-01', periods=1000, freq='1h', tz='UTC')
    
    for train_idx, test_idx in rolling_splits(idx, train=252, test=63, step=63):
        assert train_idx[-1] < test_idx[0]


def test_splits_correct_size():
    """Test that splits have correct sizes."""
    idx = pd.date_range('2023-01-01', periods=1000, freq='1h', tz='UTC')
    
    for train_idx, test_idx in rolling_splits(idx, train=252, test=63, step=63):
        assert len(train_idx) == 252
        assert len(test_idx) == 63


def test_splits_step_behavior():
    """Test that step size works correctly."""
    idx = pd.date_range('2023-01-01', periods=500, freq='1h', tz='UTC')
    
    splits = list(rolling_splits(idx, train=100, test=50, step=50))
    
    # Should have multiple splits
    assert len(splits) > 1
    
    # Each split should start 'step' periods after previous
    if len(splits) >= 2:
        train1, _ = splits[0]
        train2, _ = splits[1]
        
        # Second train should start 50 periods after first
        idx1 = idx.get_loc(train1[0])
        idx2 = idx.get_loc(train2[0])
        
        assert idx2 - idx1 == 50


def test_no_splits_if_insufficient_data():
    """Test that no splits are generated if data too small."""
    idx = pd.date_range('2023-01-01', periods=100, freq='1h', tz='UTC')
    
    splits = list(rolling_splits(idx, train=200, test=50, step=50))
    
    assert len(splits) == 0
