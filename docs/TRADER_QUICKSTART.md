# Trader Pipeline - Quick Start Guide

Get up and running with the new modular trading pipeline in 5 minutes.

## Prerequisites

- Python 3.10+
- Virtual environment activated (recommended)

## Installation

```bash
# Navigate to project root
cd c:\dev\private\apps\trading-bot-pro\CascadeProjects\tbp-v2

# Install dependencies
pip install -r requirements.txt
```

## Running Your First Backtest

### Option 1: Minimal Example (Recommended for First Run)

```bash
cd trader
python example_minimal.py
```

**What it does:**
- Generates 2000 bars of synthetic market data
- Runs walk-forward validation with Trend+Meta-AI strategy
- Prints performance metrics (Sharpe, Calmar, Win Rate, etc.)
- Saves equity curve to `example_results.csv`

**Expected output:**
```
MINIMAL EXAMPLE: Synthetic Data → Equity Curve
================================================================================
1. Generating synthetic market data...
   Generated 2000 bars from 2023-01-01 00:00:00+00:00 to 2023-03-24 07:00:00+00:00

2. Initializing components...
   ✓ Risk parameters configured
   ✓ Position sizer configured
   ✓ Signal model configured

3. Running walk-forward backtest...
   ✓ Backtest complete: XXX bars simulated

4. Performance Metrics:
   Sharpe Ratio:    X.XXX
   Calmar Ratio:    X.XXX
   Max Drawdown:    -X.XX%
   ...
```

### Option 2: Full Backtest

```bash
cd trader
python run_backtest.py
```

**What it does:**
- Loads data from `config.yaml` (or generates synthetic if no path specified)
- Runs full walk-forward validation
- Validates against Definition of Done (DoD) criteria
- Saves detailed results to `backtest_results.csv`

## Running Paper Trading

```bash
cd trader
python run_paper.py
```

**What it does:**
- Simulates live trading without real money
- Uses paper broker for position tracking
- Executes signals with stops and trailing stops
- Logs equity and positions every 24 bars

## Configuration

Edit `trader/config.yaml` to customize:

```yaml
signals:
  p_up: 0.55          # Increase for more selective signals
  
sizing:
  cap: 0.03           # Max 3% position size
  target_vol: 0.10    # Target 10% volatility

risk:
  stop_atr_mult: 2.0  # Stop at 2x ATR
  day_dd_kill: 0.08   # Kill-switch at 8% daily loss
```

## Using Real Data

### Method 1: CSV File

1. Prepare CSV with columns: `timestamp, open, high, low, close, volume`
2. Update `config.yaml`:

```yaml
data:
  path: "data/your_data.csv"
  start: "2023-01-01"
  end: "2024-01-01"
```

3. Run backtest:

```bash
python trader/run_backtest.py
```

### Method 2: Custom Loader

Create `trader/data/custom_loader.py`:

```python
import pandas as pd

def load_from_exchange(symbol: str) -> pd.DataFrame:
    # Your custom loading logic
    df = ...  # Load from API, database, etc.
    return df  # Must have: open, high, low, close, volume
```

Update `run_backtest.py` to use your loader.

## Running Tests

```bash
cd trader
pytest tests/ -v
```

**Quick test:**
```bash
pytest tests/test_features.py -v
```

**With coverage:**
```bash
pytest tests/ --cov=trader --cov-report=term-missing
```

## Understanding the Output

### Backtest Metrics Explained

- **Sharpe Ratio**: Risk-adjusted return (>1.0 is good, >2.0 is excellent)
- **Calmar Ratio**: Return per unit of max drawdown (>0.5 is good)
- **Max Drawdown**: Largest peak-to-trough decline (keep <20%)
- **Profit Factor**: Gross profit / Gross loss (>1.5 is profitable)
- **Win Rate**: % of winning trades (50-60% is typical for trend-following)
- **Turnover**: Average daily position change (lower = fewer trades)

### DoD Checks

The backtest automatically checks:
- ✓ Sharpe >= 1.0
- ✓ Calmar >= 0.5
- ✓ MaxDD < 20%
- ✓ Reproducible (seed set)
- ✓ Metrics computed

**If checks fail**: Adjust parameters in `config.yaml` or review market conditions.

## Common Workflows

### 1. Parameter Optimization

```python
# Create optimize.py
for p_up in [0.52, 0.55, 0.58, 0.60]:
    # Update config
    cfg.signals.p_up = p_up
    
    # Run backtest
    curve = walk_forward(...)
    
    # Log metrics
    print(f"p_up={p_up}: Sharpe={sharpe(...):.3f}")
```

**⚠️ Warning**: Use walk-forward to avoid overfitting!

### 2. Sensitivity Analysis

Test robustness to costs:

```yaml
# config.yaml
backtest:
  slippage_bps: 3   # Test with 0.5x slippage
  
backtest:
  slippage_bps: 12  # Test with 2x slippage
```

### 3. Multi-Symbol Backtest

Extend `run_backtest.py`:

```python
symbols = ["ES", "NQ", "YM"]
results = {}

for symbol in symbols:
    cfg.data.symbols = [symbol]
    curve = walk_forward(...)
    results[symbol] = compute_metrics(...)
```

## Integrating with Existing Bot

### Quick Integration

In your existing `trading_bot/bot.py`:

```python
# Add at top
from trader.signals.trend_meta import TrendMeta
from trader.sizing.vol_sizer import VolSizer
from trader.data.features import add_features

# In your trading loop
def generate_signal(self, df):
    # OLD: signal = self.ml_model.predict(df)
    
    # NEW: Use TrendMeta
    X = add_features(df)
    self.model = TrendMeta(p_up=0.55)
    # Train on historical data first...
    side = self.model.predict_side(X)
    conf = self.model.predict_conf(X)
    return side, conf

def calculate_position_size(self, signal, conf, atr):
    # OLD: size = self.capital * 0.02
    
    # NEW: Use VolSizer
    sizer = VolSizer(target_vol=0.10, cap=0.03)
    fraction = sizer.size_fraction(row, conf, atr)
    return self.capital * fraction
```

## Troubleshooting

### "No module named 'trader'"

**Solution**: Make sure you're running from the correct directory:
```bash
cd c:\dev\private\apps\trading-bot-pro\CascadeProjects\tbp-v2
python trader/run_backtest.py
```

### "LightGBM not installed"

**Solution**: Install LightGBM:
```bash
pip install lightgbm
```

If that fails, use XGBoost instead (edit `trend_meta.py`):
```python
from xgboost import XGBClassifier
# Replace LGBMClassifier with XGBClassifier
```

### "No backtest results generated"

**Cause**: Not enough data for walk-forward splits

**Solution**: Reduce window sizes in `config.yaml`:
```yaml
backtest:
  train_days: 100  # Reduced from 252
  test_days: 25    # Reduced from 63
```

### Low Sharpe Ratio (<0.5)

**Possible causes:**
- Trend gate too restrictive → Lower `p_up` threshold
- High costs → Check `fee_bps` and `slippage_bps` are realistic
- Sideways market → Ensure test period includes trends

## Next Steps

1. ✅ Run `example_minimal.py` to verify installation
2. ✅ Run `run_backtest.py` with synthetic data
3. ✅ Run tests: `pytest tests/ -v`
4. 📊 Load your own data via CSV or custom loader
5. 🎯 Tune parameters using walk-forward validation
6. 📈 Run paper trading for 4-8 weeks
7. 💰 Deploy to live with micro positions

## Documentation

- **Full Documentation**: `trader/README.md`
- **Implementation Spec**: See original Companion Codex spec
- **Code Examples**: `trader/example_minimal.py`
- **Tests**: `trader/tests/` (40+ unit tests)

## Support

For issues or questions:
1. Check `trader/README.md` for detailed docs
2. Review test files in `trader/tests/` for usage examples
3. Enable DEBUG logging: `logging.level = "DEBUG"` in config.yaml

---

**Happy Trading! 🚀**
