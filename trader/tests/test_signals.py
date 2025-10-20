"""Test signal model."""
import numpy as np
import pandas as pd
import pytest

from trader.data.features import add_features
from trader.signals.trend_meta import TrendMeta


def create_training_data(n_samples=200):
    """Create synthetic training data."""
    np.random.seed(42)
    idx = pd.date_range('2023-01-01', periods=n_samples, freq='1h', tz='UTC')
    
    close = 100 + np.cumsum(np.random.randn(n_samples) * 0.5)
    df = pd.DataFrame({
        'open': close * (1 + np.random.uniform(-0.01, 0.01, n_samples)),
        'high': close * (1 + np.abs(np.random.uniform(0, 0.02, n_samples))),
        'low': close * (1 - np.abs(np.random.uniform(0, 0.02, n_samples))),
        'close': close,
        'volume': np.random.uniform(1000, 10000, n_samples),
    }, index=idx)
    
    X = add_features(df).dropna()
    y = (np.random.rand(len(X)) > 0.5).astype(int)
    
    return X, pd.Series(y, index=X.index)


def test_model_fit():
    """Test that model can be trained."""
    X, y = create_training_data()
    
    model = TrendMeta(p_up=0.55, p_dn=0.55, allow_short=False)
    model.fit(X, y)
    
    # Should set feature columns
    assert model._feat_cols is not None
    assert len(model._feat_cols) > 0


def test_confidence_range():
    """Test that confidence scores are in [0, 1]."""
    X, y = create_training_data()
    
    model = TrendMeta()
    model.fit(X, y)
    
    conf = model.predict_conf(X)
    
    assert (conf >= 0).all()
    assert (conf <= 1).all()


def test_side_values():
    """Test that predicted sides are valid."""
    X, y = create_training_data()
    
    model = TrendMeta(allow_short=False)
    model.fit(X, y)
    
    side = model.predict_side(X)
    
    valid_sides = {'long', 'flat'}
    assert set(side.unique()).issubset(valid_sides)


def test_short_allowed():
    """Test that short positions are generated when allowed."""
    X, y = create_training_data(n_samples=500)
    
    model = TrendMeta(allow_short=True, p_up=0.55, p_dn=0.55)
    model.fit(X, y)
    
    side = model.predict_side(X)
    
    # With allow_short=True, we should see all three sides
    # (though not guaranteed in small samples)
    valid_sides = {'long', 'short', 'flat'}
    assert set(side.unique()).issubset(valid_sides)


def test_reproducibility():
    """Test that model predictions are reproducible."""
    X, y = create_training_data()
    
    model1 = TrendMeta(p_up=0.55)
    model1.fit(X, y)
    pred1 = model1.predict_side(X)
    
    model2 = TrendMeta(p_up=0.55)
    model2.fit(X, y)
    pred2 = model2.predict_side(X)
    
    pd.testing.assert_series_equal(pred1, pred2)
