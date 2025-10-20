#!/usr/bin/env python3
"""Minimal end-to-end example: Synthetic data → Equity curve.

This demonstrates the complete pipeline on synthetic data.
Perfect for quick validation and understanding the workflow.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from trader.backtest.engine import walk_forward
from trader.backtest.metrics import compute_metrics
from trader.data.loader import generate_synthetic_data
from trader.risk.rules import RiskParams
from trader.signals.trend_meta import TrendMeta
from trader.sizing.vol_sizer import VolSizer


def main():
    print("=" * 80)
    print("MINIMAL EXAMPLE: Synthetic Data → Equity Curve")
    print("=" * 80)
    
    # Set seed for reproducibility
    np.random.seed(42)
    
    # 1. Generate synthetic market data
    print("\n1. Generating synthetic market data...")
    df = generate_synthetic_data(
        periods=2000,
        freq="1h",
        start="2023-01-01",
        volatility=0.02,
        trend=0.0002,  # Slight upward trend
    )
    print(f"   Generated {len(df)} bars from {df.index[0]} to {df.index[-1]}")
    
    # 2. Setup components
    print("\n2. Initializing components...")
    
    risk_params = RiskParams(
        max_pos_per_asset=0.03,
        max_gross=0.6,
        stop_atr_mult=2.0,
        trail_atr_mult=3.0,
        day_dd_kill=0.08,
    )
    
    sizer = VolSizer(target_vol=0.10, cap=0.03)
    
    def build_model():
        return TrendMeta(p_up=0.55, p_dn=0.55, allow_short=False)
    
    print("   ✓ Risk parameters configured")
    print("   ✓ Position sizer configured")
    print("   ✓ Signal model configured")
    
    # 3. Run walk-forward backtest
    print("\n3. Running walk-forward backtest...")
    print("   Train: 252 periods, Test: 63 periods, Step: 63 periods")
    
    curve = walk_forward(
        df=df,
        build_model=build_model,
        sizer=sizer,
        risk=risk_params,
        fee_bps=2,
        slip_bps=6,
        train_days=252,
        test_days=63,
        step_days=63,
    )
    
    if curve.empty:
        print("   ✗ No backtest results generated!")
        return
    
    print(f"   ✓ Backtest complete: {len(curve)} bars simulated")
    
    # 4. Calculate and display metrics
    print("\n4. Performance Metrics:")
    print("-" * 80)
    
    returns = curve["equity"].pct_change().fillna(0)
    positions = curve["position"]
    
    metrics = compute_metrics(curve["equity"], returns, positions)
    
    print(f"\n   Equity Curve:")
    print(f"   Start:           ${curve['equity'].iloc[0]:,.2f}")
    print(f"   Final:           ${curve['equity'].iloc[-1]:,.2f}")
    print(f"   Total Return:    {metrics['total_return']:>8.2%}")
    
    print(f"\n   Risk-Adjusted:")
    print(f"   Sharpe Ratio:    {metrics['sharpe']:>8.3f}")
    print(f"   Calmar Ratio:    {metrics['calmar']:>8.3f}")
    print(f"   Max Drawdown:    {metrics['max_drawdown']:>8.2%}")
    
    print(f"\n   Trading:")
    print(f"   Profit Factor:   {metrics['profit_factor']:>8.3f}")
    print(f"   Win Rate:        {metrics['win_rate']:>8.2%}")
    print(f"   Avg Turnover:    {metrics['turnover']:>8.4f}")
    
    # 5. Sample equity curve data
    print("\n5. Sample Equity Curve (last 10 bars):")
    print("-" * 80)
    print(curve[['equity', 'position', 'side', 'price']].tail(10).to_string())
    
    # 6. Save results
    output_path = Path(__file__).parent.parent / "example_results.csv"
    curve.to_csv(output_path)
    print(f"\n6. Results saved to: {output_path}")
    
    # 7. Summary
    print("\n" + "=" * 80)
    print("EXAMPLE COMPLETE")
    print("=" * 80)
    print("\nNext steps:")
    print("  • Review the equity curve in example_results.csv")
    print("  • Modify parameters in this script to experiment")
    print("  • Replace synthetic data with real market data")
    print("  • Run full backtest: python trader/run_backtest.py")
    print("  • Run paper trading: python trader/run_paper.py")
    print("=" * 80)


if __name__ == "__main__":
    main()
