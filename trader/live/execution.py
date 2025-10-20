from __future__ import annotations

import logging
from typing import Literal, Optional

import pandas as pd

from trader.live.broker import IBroker
from trader.risk.rules import RiskParams, compute_stop
from trader.sizing.base import IPositionSizer


logger = logging.getLogger(__name__)


class ExecutionEngine:
    """Execute trading signals with position sizing and risk management."""
    
    def __init__(
        self,
        broker: IBroker,
        sizer: IPositionSizer,
        risk: RiskParams,
        contract_size: float = 1.0,
    ) -> None:
        self.broker = broker
        self.sizer = sizer
        self.risk = risk
        self.contract_size = contract_size
    
    def execute_signal(
        self,
        symbol: str,
        side: Literal["long", "short", "flat"],
        conf: float,
        current_data: pd.Series,
    ) -> Optional[str]:
        """Execute a trading signal.
        
        Args:
            symbol: Trading symbol
            side: Target position side
            conf: Confidence score (0-1)
            current_data: Current market data row (with OHLCV and features)
            
        Returns:
            Order ID if order placed, None otherwise
        """
        current_pos = self.broker.get_position(symbol)
        current_price = current_data.get("close", 0)
        atr = current_data.get("atr", 0)
        
        # Determine if position change needed
        current_side = current_pos.side if current_pos else "flat"
        
        if side == "flat":
            # Close position if holding
            if current_pos:
                logger.info(f"Closing {current_side} position for {symbol}")
                close_side = "sell" if current_side == "long" else "buy"
                return self.broker.place_order(
                    symbol, close_side, current_pos.size, "market"
                )
            return None
        
        if side == current_side:
            # No change needed
            return None
        
        # Calculate target position size
        equity = self.broker.get_equity()
        target_fraction = self.sizer.size_fraction(current_data, conf, atr)
        target_value = target_fraction * equity
        target_size = target_value / (current_price * self.contract_size)
        
        if target_size < 0.001:  # Minimum size threshold
            logger.warning(f"Target size too small: {target_size}")
            return None
        
        # Close existing position if switching sides
        if current_pos:
            logger.info(f"Closing {current_side} position before opening {side}")
            close_side = "sell" if current_side == "long" else "buy"
            self.broker.place_order(symbol, close_side, current_pos.size, "market")
        
        # Open new position
        logger.info(
            f"Opening {side} position for {symbol}: size={target_size:.4f}, conf={conf:.3f}"
        )
        order_side = "buy" if side == "long" else "sell"
        order_id = self.broker.place_order(symbol, order_side, target_size, "market")
        
        # Place stop-loss order
        stop_price = compute_stop(current_price, atr, side, self.risk.stop_atr_mult)
        if stop_price:
            stop_side = "sell" if side == "long" else "buy"
            self.broker.place_order(
                symbol, stop_side, target_size, "stop", stop_price=stop_price
            )
            logger.info(f"Placed stop order at {stop_price:.2f}")
        
        return order_id
    
    def update_trailing_stops(self, symbol: str, current_data: pd.Series) -> None:
        """Update trailing stops for open position.
        
        Args:
            symbol: Trading symbol
            current_data: Current market data
        """
        pos = self.broker.get_position(symbol)
        if not pos:
            return
        
        # Cancel existing stop orders
        self.broker.cancel_all(symbol)
        
        # Calculate new trailing stop
        atr = current_data.get("atr", 0)
        current_price = current_data.get("close", 0)
        
        # Simplified: use ATR-based trailing stop
        # In production, track best price since entry
        if pos.side == "long":
            stop_price = current_price - self.risk.trail_atr_mult * atr
        else:
            stop_price = current_price + self.risk.trail_atr_mult * atr
        
        # Place new trailing stop
        stop_side = "sell" if pos.side == "long" else "buy"
        self.broker.place_order(
            symbol, stop_side, pos.size, "stop", stop_price=stop_price
        )
        logger.debug(f"Updated trailing stop to {stop_price:.2f}")
