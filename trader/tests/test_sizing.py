"""Test position sizing."""
import numpy as np
import pandas as pd
import pytest

from trader.sizing.vol_sizer import VolSizer


def test_sizer_respects_cap():
    """Test that sizer never exceeds cap."""
    sizer = VolSizer(target_vol=0.20, cap=0.03)
    
    row = pd.Series({'atr': 0.01})
    
    # Even with high volatility target and confidence, should cap
    size = sizer.size_fraction(row, conf=1.0, atr=0.01)
    
    assert size <= 0.03


def test_sizer_zero_on_zero_atr():
    """Test that sizer returns 0 when ATR is 0."""
    sizer = VolSizer(target_vol=0.10, cap=0.03)
    
    row = pd.Series({'atr': 0.0})
    size = sizer.size_fraction(row, conf=0.8, atr=0.0)
    
    assert size == 0.0


def test_sizer_zero_on_negative_atr():
    """Test that sizer returns 0 when ATR is negative."""
    sizer = VolSizer(target_vol=0.10, cap=0.03)
    
    row = pd.Series({'atr': -0.01})
    size = sizer.size_fraction(row, conf=0.8, atr=-0.01)
    
    assert size == 0.0


def test_sizer_zero_on_zero_confidence():
    """Test that sizer returns 0 when confidence is 0."""
    sizer = VolSizer(target_vol=0.10, cap=0.03)
    
    row = pd.Series({'atr': 0.02})
    size = sizer.size_fraction(row, conf=0.0, atr=0.02)
    
    assert size == 0.0


def test_sizer_scales_with_confidence():
    """Test that size scales with confidence."""
    sizer = VolSizer(target_vol=0.10, cap=0.10)
    
    row = pd.Series({'atr': 0.02})
    
    size_low = sizer.size_fraction(row, conf=0.5, atr=0.02)
    size_high = sizer.size_fraction(row, conf=1.0, atr=0.02)
    
    assert size_high > size_low
    assert abs(size_high - 2 * size_low) < 0.001


def test_sizer_inverse_volatility():
    """Test that size is inversely proportional to volatility."""
    sizer = VolSizer(target_vol=0.10, cap=0.10)
    
    row = pd.Series({})
    
    size_low_vol = sizer.size_fraction(row, conf=1.0, atr=0.01)
    size_high_vol = sizer.size_fraction(row, conf=1.0, atr=0.02)
    
    # Higher volatility should give smaller position
    assert size_low_vol > size_high_vol
