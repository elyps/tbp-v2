# Trading Pipeline - Companion Codex Implementation

Modular, production-ready trading pipeline with **Trend + Meta-AI signals**, **volatility-based sizing**, and **comprehensive risk management**.

## Overview

This implementation follows the "Companion Codex" specification for building a robust algorithmic trading system with:

- **Hybrid Signal Model**: Trend-following gate + LightGBM meta-classifier for edge detection
- **Volatility-Based Position Sizing**: ATR-scaled positions with confidence weighting
- **Multi-Layer Risk Controls**: ATR stops, trailing stops, portfolio limits, and kill-switch
- **Walk-Forward Validation**: Realistic out-of-sample testing with transaction costs
- **Live Trading Support**: Paper trading with order execution and position management

## Directory Structure

```
trader/
├── data/
│   ├── features.py       # Feature engineering (EMA, MACD, ATR, RSI, etc.)
│   └── loader.py         # Data loading utilities
├── signals/
│   ├── base.py           # Signal model interface
│   └── trend_meta.py     # Hybrid Trend + Meta-AI model
├── sizing/
│   ├── base.py           # Position sizer interface
│   ├── vol_sizer.py      # Volatility-based sizer
│   └── rl_sizer.py       # RL sizer placeholder (future)
├── risk/
│   ├── rules.py          # Risk parameters and stop calculations
│   └── portfolio.py      # Portfolio risk manager with kill-switch
├── backtest/
│   ├── engine.py         # Simulation and walk-forward engine
│   ├── metrics.py        # Performance metrics (Sharpe, Calmar, etc.)
│   └── costs.py          # Transaction cost model
├── live/
│   ├── broker.py         # Broker interface and paper broker
│   └── execution.py      # Order execution engine
├── utils/
│   ├── config.py         # Configuration management
│   └── split.py          # Walk-forward split utilities
├── tests/                # Unit tests (10+ test modules)
├── config.yaml           # Configuration file
├── run_backtest.py       # Backtest orchestration script
└── run_paper.py          # Paper trading script
```

## Quick Start

### 1. Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Or install just the new requirements
pip install pydantic pyyaml scipy pytest pytest-cov
```

### 2. Run Backtest

```bash
cd trader
python run_backtest.py
```

This will:
- Load or generate market data
- Run walk-forward validation (train: 252 days, test: 63 days)
- Train TrendMeta model on each training window
- Simulate trading with realistic costs
- Print performance metrics (Sharpe, Calmar, MaxDD, etc.)
- Save results to `backtest_results.csv`

### 3. Run Paper Trading

```bash
cd trader
python run_paper.py
```

This simulates live trading with:
- Paper broker (no real money)
- Real-time signal generation
- Position sizing and risk management
- Stop-loss and trailing stop execution

### 4. Run Tests

```bash
cd trader
pytest tests/ -v --cov=trader --cov-report=term-missing
```

Tests cover:
- Feature determinism and bounds checking
- Signal model output validation
- Position sizing constraints
- Risk rule calculations
- Cost application
- Walk-forward split logic
- Performance metrics

## Configuration

Edit `config.yaml` to customize:

```yaml
data:
  symbols: ["ES"]           # Trading symbols
  bar: "1h"                 # Bar frequency
  # path: "data.csv"        # Optional: CSV file path

backtest:
  train_days: 252           # Training window (days)
  test_days: 63             # Test window (days)
  fee_bps: 2                # Fees (basis points)
  slippage_bps: 6           # Slippage (basis points)

signals:
  type: "trend_meta"        # Signal model type
  p_up: 0.55                # Long entry threshold
  p_dn: 0.55                # Short entry threshold
  allow_short: false        # Enable short positions

sizing:
  type: "vol"               # Sizer type
  target_vol: 0.10          # Target volatility (10%)
  cap: 0.03                 # Max position size (3%)

risk:
  max_pos_per_asset: 0.03   # Max 3% per position
  max_gross: 0.6            # Max 60% gross exposure
  stop_atr_mult: 2.0        # Stop: 2x ATR
  trail_atr_mult: 3.0       # Trailing: 3x ATR
  day_dd_kill: 0.08         # Kill-switch: 8% daily DD

logging:
  level: "INFO"             # Log level
  seed: 42                  # Random seed
```

## Core Components

### Signal Model: TrendMeta

Hybrid approach combining:
1. **Trend Gate**: Only trade when `ema50 > ema200`, `macd > signal`, and ATR above median
2. **Meta-Classifier**: LightGBM model predicts edge probability within trend regime

```python
from trader.signals.trend_meta import TrendMeta

model = TrendMeta(p_up=0.55, p_dn=0.55, allow_short=False)
model.fit(X_train, y_train)

side = model.predict_side(X_test)  # "long", "short", or "flat"
conf = model.predict_conf(X_test)  # 0.0 to 1.0
```

### Position Sizing: VolSizer

Scales position by:
- **Inverse volatility**: Higher ATR → smaller position
- **Confidence**: Higher ML confidence → larger position
- **Hard cap**: Never exceeds max position limit

```python
from trader.sizing.vol_sizer import VolSizer

sizer = VolSizer(target_vol=0.10, cap=0.03)
fraction = sizer.size_fraction(row, conf=0.8, atr=0.02)
```

### Risk Management

**Stop-Loss**: `entry_price - (stop_atr_mult × ATR)` for longs

**Trailing Stop**: Follows best price at `trail_atr_mult × ATR` distance

**Portfolio Limits**:
- Max 3% per position
- Max 60% gross exposure
- Daily drawdown kill-switch at 8%

**Kill-Switch**: Flatten all positions if intraday loss > 8% of equity

### Walk-Forward Validation

```python
from trader.backtest.engine import walk_forward

curve = walk_forward(
    df=market_data,
    build_model=lambda: TrendMeta(...),
    sizer=VolSizer(...),
    risk=RiskParams(...),
    fee_bps=2,
    slip_bps=6,
)
```

Generates out-of-sample equity curve across rolling windows.

## Definition of Done (DoD)

✅ **Reproducible Results**: Fixed random seed, deterministic features
✅ **Metrics Computed**: Sharpe, Calmar, MaxDD, PF, Turnover, Win Rate
✅ **Cost Model**: Realistic fees (2 bps) + slippage (6 bps)
✅ **Unit Tests**: 40+ tests covering all core components
✅ **Walk-Forward**: OOS validation with 252/63 day windows
✅ **Risk Controls**: Stops, trailing, position limits, kill-switch
✅ **Configurable**: All parameters in `config.yaml`
✅ **Structured Logs**: INFO-level logging with timestamps

**Target Performance** (adjust for market):
- Sharpe ≥ 1.0 (OOS)
- Calmar ≥ 0.5 (OOS)
- MaxDD < 20% (OOS)

## Usage Examples

### Custom Data Loading

```python
# In config.yaml, specify CSV path:
data:
  path: "data/ES_1h.csv"
  start: "2023-01-01"
  end: "2024-01-01"

# CSV format: timestamp, open, high, low, close, volume
```

### Parameter Tuning

Grid search (use walk-forward to avoid overfitting):

```python
for p_up in [0.52, 0.55, 0.58, 0.60]:
    for cap in [0.02, 0.03, 0.04]:
        for stop_mult in [1.5, 2.0, 2.5]:
            # Update config and run backtest
            ...
```

### Integrating with Existing Bot

Map the pipeline to your existing structure:

```python
# Your existing code:
# features = generate_features(df)
# signal = generate_signal(features)
# execute_orders(signal)

# New pipeline integration:
from trader.data.features import add_features
from trader.signals.trend_meta import TrendMeta
from trader.sizing.vol_sizer import VolSizer
from trader.live.execution import ExecutionEngine

# Replace generate_features:
X = add_features(df)

# Replace generate_signal:
model = TrendMeta(...)
side = model.predict_side(X)
conf = model.predict_conf(X)

# Replace execute_orders:
execution = ExecutionEngine(broker, sizer, risk_params)
execution.execute_signal(symbol, side, conf, current_data)
```

## Rollout Plan

**Phase 1 - Backtest OK** (1-2 weeks):
- All tests passing ✅
- Metrics meet DoD targets ✅
- Sensitivity analysis (fees × 0.5, 1.0, 2.0)

**Phase 2 - Paper Trading** (4-8 weeks):
- Shadow mode: log signals without real trades
- Compare paper vs. live fills
- Monitor slippage and execution quality

**Phase 3 - Small Live** (2-4 weeks):
- Micro position sizes (0.1% of capital)
- Daily kill-switch active
- Manual monitoring

**Phase 4 - Scale Up**:
- Gradually increase position sizes
- Only if:
  - Stable slippage < 8 bps
  - Drawdowns within limits
  - No unexpected model behavior

## Edge Cases & Guards

✅ **Data Gaps**: Forward-fill non-price fields only; drop extreme outliers
✅ **Regime Breaks**: Optional volatility scaling when vol20 spikes
✅ **Cost Stress**: Test with slippage × {0.5, 1.0, 2.0}
✅ **Leakage Prevention**: All features use `.shift()` where needed
✅ **Micro-ATR**: Minimum tick size and contract size handling

## Advanced Features (Optional)

### RL-Based Sizing (Future)

```python
from trader.sizing.rl_sizer import RLSizer

# Placeholder for PPO/SAC-based position sizing
sizer = RLSizer(target_vol=0.10, cap=0.03)
```

### Multi-Asset Portfolio

Extend `simulate()` to handle multiple symbols:

```python
positions = {
    'ES': 0.02,
    'NQ': 0.015,
    'GC': 0.01,
}
```

### Feature Selection

Use permutation importance to reduce overfitting:

```python
from sklearn.inspection import permutation_importance

# After training:
result = permutation_importance(model.clf, X_val, y_val)
top_features = X.columns[result.importances_mean.argsort()[-10:]]
```

## Troubleshooting

**Issue**: "Model not fit" error
- **Solution**: Ensure `model.fit()` is called before `predict_side()`

**Issue**: Low Sharpe ratio in backtest
- **Solution**: Check if trend gate is too restrictive; try lowering `p_up` threshold

**Issue**: High turnover
- **Solution**: Increase `p_up` to reduce signal frequency; adjust step size

**Issue**: Tests failing on Windows
- **Solution**: Ensure UTC timezone handling in all datetime operations

## References

- **LightGBM**: https://lightgbm.readthedocs.io/
- **Walk-Forward Analysis**: Pardo (2008) "The Evaluation and Optimization of Trading Strategies"
- **ATR-Based Stops**: Wilder (1978) "New Concepts in Technical Trading Systems"

## License

Part of the `tbp-v2` trading bot project.

---

**Author**: Companion Codex Implementation
**Version**: 1.0.0
**Last Updated**: 2025-10-19
