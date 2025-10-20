#!/usr/bin/env python3
"""Run walk-forward backtest."""
from __future__ import annotations

import logging
import sys
from pathlib import Path

import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from trader.backtest.engine import walk_forward
from trader.backtest.metrics import compute_metrics, max_drawdown, sharpe, calmar
from trader.data.loader import load_market_data
from trader.risk.rules import RiskParams
from trader.signals.trend_meta import TrendMeta
from trader.sizing.vol_sizer import VolSizer
from trader.utils.config import load_cfg


def build_model_from_cfg(cfg):
    """Build signal model from configuration."""
    return TrendMeta(
        p_up=cfg.signals.p_up,
        p_dn=cfg.signals.p_dn,
        allow_short=cfg.signals.allow_short,
    )


def main():
    # Load configuration
    config_path = Path(__file__).parent / "config.yaml"
    cfg = load_cfg(config_path)
    
    # Set random seed for reproducibility
    np.random.seed(cfg.logging.seed)
    
    # Setup logging
    logging.basicConfig(
        level=cfg.logging.level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    )
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 80)
    logger.info("Starting Walk-Forward Backtest")
    logger.info("=" * 80)
    
    # Load market data
    logger.info("Loading market data...")
    df = load_market_data(cfg)
    logger.info(f"Loaded {len(df)} bars from {df.index[0]} to {df.index[-1]}")
    
    # Initialize components
    risk_params = RiskParams(
        max_pos_per_asset=cfg.risk.max_pos_per_asset,
        max_gross=cfg.risk.max_gross,
        stop_atr_mult=cfg.risk.stop_atr_mult,
        trail_atr_mult=cfg.risk.trail_atr_mult,
        day_dd_kill=cfg.risk.day_dd_kill,
    )
    sizer = VolSizer(cfg.sizing.target_vol, cfg.sizing.cap)
    
    # Run walk-forward validation
    logger.info("Running walk-forward validation...")
    logger.info(f"Train: {cfg.backtest.train_days} days, Test: {cfg.backtest.test_days} days, Step: {cfg.backtest.step_days} days")
    
    curve = walk_forward(
        df,
        lambda: build_model_from_cfg(cfg),
        sizer,
        risk_params,
        cfg.backtest.fee_bps,
        cfg.backtest.slippage_bps,
        cfg.backtest.train_days,
        cfg.backtest.test_days,
        cfg.backtest.step_days,
    )
    
    if curve.empty:
        logger.error("No backtest results generated!")
        return
    
    # Calculate metrics
    logger.info("\n" + "=" * 80)
    logger.info("BACKTEST RESULTS")
    logger.info("=" * 80)
    
    returns = curve["equity"].pct_change().fillna(0)
    positions = curve["position"]
    
    metrics = compute_metrics(curve["equity"], returns, positions)
    
    logger.info(f"\nEquity Curve:")
    logger.info(f"  Start Equity:    ${curve['equity'].iloc[0]:,.2f}")
    logger.info(f"  Final Equity:    ${curve['equity'].iloc[-1]:,.2f}")
    logger.info(f"  Total Return:    {metrics['total_return']:.2%}")
    
    logger.info(f"\nRisk Metrics:")
    logger.info(f"  Sharpe Ratio:    {metrics['sharpe']:.3f}")
    logger.info(f"  Calmar Ratio:    {metrics['calmar']:.3f}")
    logger.info(f"  Max Drawdown:    {metrics['max_drawdown']:.2%}")
    
    logger.info(f"\nTrading Metrics:")
    logger.info(f"  Profit Factor:   {metrics['profit_factor']:.3f}")
    logger.info(f"  Win Rate:        {metrics['win_rate']:.2%}")
    logger.info(f"  Avg Turnover:    {metrics['turnover']:.4f}")
    
    logger.info(f"\nPeriod:")
    logger.info(f"  Start:           {curve.index[0]}")
    logger.info(f"  End:             {curve.index[-1]}")
    logger.info(f"  Bars:            {len(curve)}")
    
    # Save results
    output_path = Path(__file__).parent.parent / "backtest_results.csv"
    curve.to_csv(output_path)
    logger.info(f"\nResults saved to: {output_path}")
    
    # Definition of Done checks
    logger.info("\n" + "=" * 80)
    logger.info("DEFINITION OF DONE (DoD) CHECKS")
    logger.info("=" * 80)
    
    checks = {
        "Sharpe >= 1.0": metrics['sharpe'] >= 1.0,
        "Calmar >= 0.5": metrics['calmar'] >= 0.5,
        "MaxDD < 20%": abs(metrics['max_drawdown']) < 0.20,
        "Reproducible (seed set)": True,  # Seed is set
        "Metrics computed": True,
    }
    
    for check, passed in checks.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        logger.info(f"  {status}: {check}")
    
    all_passed = all(checks.values())
    logger.info("\n" + "=" * 80)
    if all_passed:
        logger.info("✓ All DoD checks PASSED")
    else:
        logger.warning("⚠ Some DoD checks FAILED - review parameters")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
