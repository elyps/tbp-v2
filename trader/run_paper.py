#!/usr/bin/env python3
"""Run paper trading with live simulation."""
from __future__ import annotations

import logging
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from trader.data.features import add_features
from trader.data.loader import generate_synthetic_data
from trader.live.broker import PaperBroker
from trader.live.execution import ExecutionEngine
from trader.risk.rules import RiskParams
from trader.signals.trend_meta import TrendMeta
from trader.sizing.vol_sizer import VolSizer
from trader.utils.config import load_cfg


def main():
    # Load configuration
    config_path = Path(__file__).parent / "config.yaml"
    cfg = load_cfg(config_path)
    
    # Set random seed
    np.random.seed(cfg.logging.seed)
    
    # Setup logging
    logging.basicConfig(
        level=cfg.logging.level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    )
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 80)
    logger.info("Starting Paper Trading")
    logger.info("=" * 80)
    
    # Initialize components
    broker = PaperBroker(initial_balance=10000.0)
    risk_params = RiskParams(
        max_pos_per_asset=cfg.risk.max_pos_per_asset,
        max_gross=cfg.risk.max_gross,
        stop_atr_mult=cfg.risk.stop_atr_mult,
        trail_atr_mult=cfg.risk.trail_atr_mult,
        day_dd_kill=cfg.risk.day_dd_kill,
    )
    sizer = VolSizer(cfg.sizing.target_vol, cfg.sizing.cap)
    execution = ExecutionEngine(broker, sizer, risk_params, contract_size=1.0)
    
    # Initialize model
    logger.info("Initializing model...")
    model = TrendMeta(
        p_up=cfg.signals.p_up,
        p_dn=cfg.signals.p_dn,
        allow_short=cfg.signals.allow_short,
    )
    
    # Generate synthetic data for demonstration
    # In production, replace with real data feed
    logger.info("Generating synthetic market data...")
    df = generate_synthetic_data(periods=1000, freq="1h")
    
    # Train model on initial data
    train_window = cfg.backtest.train_days
    df_train = df.iloc[:train_window]
    X_train = add_features(df_train).dropna()
    
    # Create simple labels for training
    y_train = (df_train['close'].pct_change(10).shift(-10) > 0.001).astype(int)
    y_train = y_train.reindex(X_train.index).dropna()
    X_train = X_train.loc[y_train.index]
    
    logger.info(f"Training model on {len(X_train)} bars...")
    model.fit(X_train, y_train)
    logger.info("Model trained successfully")
    
    # Paper trading loop
    logger.info("\nStarting paper trading simulation...")
    logger.info("=" * 80)
    
    symbol = cfg.data.symbols[0] if cfg.data.symbols else "SYNTHETIC"
    
    # Simulate real-time trading on remaining data
    for i in range(train_window, len(df)):
        current_bar = df.iloc[i]
        timestamp = df.index[i]
        
        # Add features to current bar
        history = df.iloc[max(0, i-200):i+1]  # Keep enough history for features
        X = add_features(history)
        
        if X.empty or timestamp not in X.index:
            continue
        
        current_features = X.loc[timestamp]
        
        # Generate signal
        side = model.predict_side(pd.DataFrame([current_features]))[0]
        conf = model.predict_conf(pd.DataFrame([current_features]))[0]
        
        # Update broker with current prices
        broker.update_prices({symbol: current_bar['close']})
        
        # Execute signal
        if side != "flat":
            execution.execute_signal(symbol, side, conf, current_features)
        else:
            # Close position if signal is flat
            pos = broker.get_position(symbol)
            if pos:
                logger.info(f"[{timestamp}] Closing position (signal: flat)")
                execution.execute_signal(symbol, "flat", 0.0, current_features)
        
        # Update trailing stops
        if broker.get_position(symbol):
            execution.update_trailing_stops(symbol, current_features)
        
        # Log status every 24 bars (1 day for hourly data)
        if i % 24 == 0:
            equity = broker.get_equity()
            positions = broker.get_all_positions()
            logger.info(
                f"[{timestamp}] Equity: ${equity:,.2f} | "
                f"Positions: {len(positions)} | "
                f"Last Signal: {side} (conf={conf:.3f})"
            )
        
        # Simulate real-time delay (remove in production)
        # time.sleep(0.01)
    
    # Final report
    logger.info("\n" + "=" * 80)
    logger.info("PAPER TRADING SUMMARY")
    logger.info("=" * 80)
    
    final_equity = broker.get_equity()
    total_return = (final_equity / 10000.0 - 1) * 100
    
    logger.info(f"Initial Balance:  $10,000.00")
    logger.info(f"Final Equity:     ${final_equity:,.2f}")
    logger.info(f"Total Return:     {total_return:+.2f}%")
    logger.info(f"Open Positions:   {len(broker.get_all_positions())}")
    
    logger.info("\n" + "=" * 80)
    logger.info("Paper trading simulation complete")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
