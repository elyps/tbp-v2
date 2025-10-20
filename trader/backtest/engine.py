from __future__ import annotations

from typing import Callable

import numpy as np
import pandas as pd

from trader.backtest.costs import apply_costs
from trader.data.features import add_features, label_forward_return
from trader.risk.portfolio import PortfolioRiskManager
from trader.risk.rules import RiskParams, compute_stop, compute_trailing_stop
from trader.sizing.base import IPositionSizer
from trader.utils.split import rolling_splits


def simulate(
    df: pd.DataFrame,
    side: pd.Series,
    conf: pd.Series,
    sizer: IPositionSizer,
    risk: RiskParams,
    fee_bps: int = 2,
    slip_bps: int = 6,
    initial_equity: float = 10000.0,
) -> pd.DataFrame:
    """Simulate trading with stops, trailing, and risk controls.
    
    Args:
        df: Market data with OHLCV and features
        side: Series of position sides ("long", "short", "flat")
        conf: Series of confidence scores (0-1)
        sizer: Position sizer instance
        risk: Risk parameters
        fee_bps: Trading fee in basis points
        slip_bps: Slippage in basis points
        initial_equity: Starting equity
        
    Returns:
        DataFrame with equity curve, positions, and trade details
    """
    equity = initial_equity
    position = 0.0  # Current position size (fraction of equity)
    position_side = "flat"
    entry_price = 0.0
    entry_atr = 0.0
    stop_price = None
    best_price = None
    
    results = []
    risk_mgr = PortfolioRiskManager(risk)
    start_of_day_equity = equity
    
    for idx, row in df.iterrows():
        current_price = row.get("close", 0)
        atr = row.get("atr", 0)
        
        # Check daily drawdown kill-switch
        if risk_mgr.check_daily_drawdown(equity, start_of_day_equity, idx):
            # Flatten position
            if position != 0:
                exit_value = position * equity
                pnl_gross = (current_price / entry_price - 1) * exit_value if position_side == "long" else (entry_price / current_price - 1) * exit_value
                pnl_net = apply_costs(pnl_gross, fee_bps, slip_bps, abs(exit_value))
                equity += pnl_net
                position = 0.0
                position_side = "flat"
                stop_price = None
                best_price = None
        
        # Reset daily equity tracking at day boundaries
        if idx.hour == 0 and idx.minute == 0:  # Assuming intraday data
            start_of_day_equity = equity
            risk_mgr.reset_kill_switch()
        
        # Check stops if in position
        if position != 0 and stop_price is not None:
            hit_stop = False
            
            # Update trailing stop
            if best_price is not None:
                if position_side == "long":
                    best_price = max(best_price, row.get("high", current_price))
                    new_trail = compute_trailing_stop(
                        current_price, best_price, atr, "long", risk.trail_atr_mult
                    )
                    if new_trail and new_trail > stop_price:
                        stop_price = new_trail
                    if row.get("low", current_price) <= stop_price:
                        hit_stop = True
                        exit_price = stop_price
                elif position_side == "short":
                    best_price = min(best_price, row.get("low", current_price))
                    new_trail = compute_trailing_stop(
                        current_price, best_price, atr, "short", risk.trail_atr_mult
                    )
                    if new_trail and new_trail < stop_price:
                        stop_price = new_trail
                    if row.get("high", current_price) >= stop_price:
                        hit_stop = True
                        exit_price = stop_price
            else:
                # Initial stop (no trailing yet)
                if position_side == "long" and row.get("low", current_price) <= stop_price:
                    hit_stop = True
                    exit_price = stop_price
                elif position_side == "short" and row.get("high", current_price) >= stop_price:
                    hit_stop = True
                    exit_price = stop_price
            
            if hit_stop:
                exit_value = position * equity
                pnl_gross = (exit_price / entry_price - 1) * exit_value if position_side == "long" else (entry_price / exit_price - 1) * exit_value
                pnl_net = apply_costs(pnl_gross, fee_bps, slip_bps, abs(exit_value))
                equity += pnl_net
                position = 0.0
                position_side = "flat"
                stop_price = None
                best_price = None
        
        # Get target side and position
        target_side = side.get(idx, "flat")
        target_conf = conf.get(idx, 0.0)
        
        # Determine position change
        if target_side == "flat" or target_conf <= 0:
            # Exit position if holding
            if position != 0:
                exit_value = position * equity
                pnl_gross = (current_price / entry_price - 1) * exit_value if position_side == "long" else (entry_price / current_price - 1) * exit_value
                pnl_net = apply_costs(pnl_gross, fee_bps, slip_bps, abs(exit_value))
                equity += pnl_net
                position = 0.0
                position_side = "flat"
                stop_price = None
                best_price = None
        elif target_side != position_side:
            # Side change - exit old, enter new
            if position != 0:
                exit_value = position * equity
                pnl_gross = (current_price / entry_price - 1) * exit_value if position_side == "long" else (entry_price / current_price - 1) * exit_value
                pnl_net = apply_costs(pnl_gross, fee_bps, slip_bps, abs(exit_value))
                equity += pnl_net
                position = 0.0
            
            # Enter new position
            target_fraction = sizer.size_fraction(row, target_conf, atr)
            target_fraction = risk_mgr.check_position_size(
                "asset", target_fraction, {}
            )
            target_fraction = risk_mgr.check_gross_exposure(target_fraction, {})
            
            if target_fraction > 0:
                position = target_fraction
                position_side = target_side
                entry_price = row.get("open", current_price)  # Enter at next bar open
                entry_atr = atr
                stop_price = compute_stop(entry_price, entry_atr, position_side, risk.stop_atr_mult)
                best_price = entry_price
                
                # Apply entry costs
                entry_value = position * equity
                entry_cost = apply_costs(0, fee_bps, slip_bps, abs(entry_value))
                equity += entry_cost
        
        results.append({
            "timestamp": idx,
            "equity": equity,
            "position": position,
            "side": position_side,
            "price": current_price,
            "stop": stop_price,
        })
    
    return pd.DataFrame(results).set_index("timestamp")


def walk_forward(
    df: pd.DataFrame,
    build_model: Callable,
    sizer: IPositionSizer,
    risk: RiskParams,
    fee_bps: int = 2,
    slip_bps: int = 6,
    train_days: int = 252,
    test_days: int = 63,
    step_days: int = 63,
) -> pd.DataFrame:
    """Run walk-forward validation.
    
    Args:
        df: Market data with OHLCV
        build_model: Callable that returns a new signal model instance
        sizer: Position sizer instance
        risk: Risk parameters
        fee_bps: Trading fee in basis points
        slip_bps: Slippage in basis points
        train_days: Training window size
        test_days: Test window size
        step_days: Step size between splits
        
    Returns:
        Combined equity curve across all test periods
    """
    curves = []
    
    for train_idx, test_idx in rolling_splits(df.index, train_days, test_days, step_days):
        df_train = df.loc[train_idx]
        df_test = df.loc[test_idx]
        
        # Add features
        X_train = add_features(df_train)
        y_train = label_forward_return(df_train)
        X_test = add_features(df_test)
        
        # Align labels with features (drop NaNs)
        X_train_clean = X_train.dropna()
        y_train_clean = y_train.reindex(X_train_clean.index).dropna()
        X_train_clean = X_train_clean.loc[y_train_clean.index]
        
        if len(X_train_clean) == 0 or len(y_train_clean) == 0:
            continue
        
        # Train model
        model = build_model()
        model.fit(X_train_clean, y_train_clean)
        
        # Predict on test set
        X_test_clean = X_test.dropna()
        if len(X_test_clean) == 0:
            continue
            
        side = model.predict_side(X_test_clean)
        conf = model.predict_conf(X_test_clean)
        
        # Simulate trading
        df_test_aligned = df_test.loc[side.index]
        curve = simulate(
            df_test_aligned, side, conf, sizer, risk, fee_bps, slip_bps
        )
        
        curves.append(curve)
    
    if not curves:
        return pd.DataFrame()
    
    return pd.concat(curves)
