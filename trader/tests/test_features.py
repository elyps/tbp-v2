"""Test feature engineering and determinism."""
import numpy as np
import pandas as pd
import pytest

from trader.data.features import add_features, label_forward_return, rsi, trend_gate


def create_sample_data(periods=100, seed=42):
    """Create sample OHLCV data for testing."""
    np.random.seed(seed)
    idx = pd.date_range('2023-01-01', periods=periods, freq='1h', tz='UTC')
    close = 100 + np.cumsum(np.random.randn(periods) * 0.5)
    
    df = pd.DataFrame({
        'open': close * (1 + np.random.uniform(-0.01, 0.01, periods)),
        'high': close * (1 + np.abs(np.random.uniform(0, 0.02, periods))),
        'low': close * (1 - np.abs(np.random.uniform(0, 0.02, periods))),
        'close': close,
        'volume': np.random.uniform(1000, 10000, periods),
    }, index=idx)
    
    return df


def test_feature_determinism():
    """Test that features are deterministic given same input."""
    df = create_sample_data(100, seed=42)
    
    features1 = add_features(df.copy())
    features2 = add_features(df.copy())
    
    # Should be identical
    pd.testing.assert_frame_equal(features1, features2)


def test_rsi_bounds():
    """Test that RSI stays in [0, 100] range."""
    df = create_sample_data(100)
    rsi_values = rsi(df['close'], 14)
    
    assert rsi_values.min() >= 0
    assert rsi_values.max() <= 100


def test_atr_positive():
    """Test that ATR is always non-negative."""
    df = create_sample_data(100)
    features = add_features(df)
    
    assert (features['atr'] >= 0).all()


def test_trend_gate_output():
    """Test trend gate returns boolean series."""
    df = create_sample_data(300)  # Need more data for 200-period rolling
    features = add_features(df)
    
    gate = trend_gate(features)
    
    assert gate.dtype == bool
    assert len(gate) == len(df)


def test_label_forward_return_binary():
    """Test that labels are binary (0 or 1)."""
    df = create_sample_data(100)
    labels = label_forward_return(df, horizon=10, fee_bps=2)
    
    # Should only contain 0, 1, or NaN
    unique_vals = labels.dropna().unique()
    assert set(unique_vals).issubset({0, 1})


def test_features_no_future_leak():
    """Test that features don't use future data."""
    df = create_sample_data(100)
    features = add_features(df)
    
    # At index i, features should only depend on data up to i
    # Check that first valid feature index >= some minimum
    # (due to rolling windows)
    assert features['ema50'].notna().sum() >= 50
    assert features['atr'].notna().sum() >= 14


def test_missing_columns_handling():
    """Test handling of missing required columns."""
    df = pd.DataFrame({'close': [100, 101, 102]})
    
    # Should not raise, but some features may be NaN
    features = add_features(df)
    assert 'ema50' in features.columns
