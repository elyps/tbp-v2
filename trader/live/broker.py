from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Literal, Optional


@dataclass
class Position:
    symbol: str
    side: Literal["long", "short"]
    size: float
    entry_price: float
    current_price: float
    pnl: float


@dataclass
class Order:
    symbol: str
    side: Literal["buy", "sell"]
    size: float
    order_type: Literal["market", "limit", "stop"]
    price: Optional[float] = None
    stop_price: Optional[float] = None
    trail_amount: Optional[float] = None


class IBroker(ABC):
    """Abstract broker interface."""
    
    @abstractmethod
    def get_position(self, symbol: str) -> Optional[Position]:
        """Get current position for symbol."""
        pass
    
    @abstractmethod
    def get_all_positions(self) -> Dict[str, Position]:
        """Get all open positions."""
        pass
    
    @abstractmethod
    def place_order(
        self,
        symbol: str,
        side: Literal["buy", "sell"],
        size: float,
        order_type: Literal["market", "limit", "stop"] = "market",
        price: Optional[float] = None,
        stop_price: Optional[float] = None,
        trail_amount: Optional[float] = None,
    ) -> str:
        """Place an order. Returns order ID."""
        pass
    
    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order."""
        pass
    
    @abstractmethod
    def cancel_all(self, symbol: Optional[str] = None) -> int:
        """Cancel all orders for symbol (or all if None)."""
        pass
    
    @abstractmethod
    def get_equity(self) -> float:
        """Get current account equity."""
        pass
    
    @abstractmethod
    def get_balance(self) -> float:
        """Get current account balance."""
        pass


class PaperBroker(IBroker):
    """Paper trading broker (simulation)."""
    
    def __init__(self, initial_balance: float = 10000.0) -> None:
        self.balance = initial_balance
        self.equity = initial_balance
        self.positions: Dict[str, Position] = {}
        self.orders: Dict[str, Order] = {}
        self._next_order_id = 1
    
    def get_position(self, symbol: str) -> Optional[Position]:
        return self.positions.get(symbol)
    
    def get_all_positions(self) -> Dict[str, Position]:
        return self.positions.copy()
    
    def place_order(
        self,
        symbol: str,
        side: Literal["buy", "sell"],
        size: float,
        order_type: Literal["market", "limit", "stop"] = "market",
        price: Optional[float] = None,
        stop_price: Optional[float] = None,
        trail_amount: Optional[float] = None,
    ) -> str:
        order_id = f"order_{self._next_order_id}"
        self._next_order_id += 1
        
        order = Order(
            symbol=symbol,
            side=side,
            size=size,
            order_type=order_type,
            price=price,
            stop_price=stop_price,
            trail_amount=trail_amount,
        )
        self.orders[order_id] = order
        return order_id
    
    def cancel_order(self, order_id: str) -> bool:
        if order_id in self.orders:
            del self.orders[order_id]
            return True
        return False
    
    def cancel_all(self, symbol: Optional[str] = None) -> int:
        if symbol is None:
            count = len(self.orders)
            self.orders.clear()
            return count
        
        to_remove = [oid for oid, o in self.orders.items() if o.symbol == symbol]
        for oid in to_remove:
            del self.orders[oid]
        return len(to_remove)
    
    def get_equity(self) -> float:
        return self.equity
    
    def get_balance(self) -> float:
        return self.balance
    
    def update_position(
        self, symbol: str, side: Literal["long", "short"], size: float, price: float
    ) -> None:
        """Update position (for paper trading simulation)."""
        if size == 0:
            if symbol in self.positions:
                del self.positions[symbol]
        else:
            self.positions[symbol] = Position(
                symbol=symbol,
                side=side,
                size=size,
                entry_price=price,
                current_price=price,
                pnl=0.0,
            )
    
    def update_prices(self, prices: Dict[str, float]) -> None:
        """Update current prices for positions."""
        for symbol, pos in self.positions.items():
            if symbol in prices:
                pos.current_price = prices[symbol]
                if pos.side == "long":
                    pos.pnl = (pos.current_price - pos.entry_price) * pos.size
                else:
                    pos.pnl = (pos.entry_price - pos.current_price) * pos.size
        
        total_pnl = sum(p.pnl for p in self.positions.values())
        self.equity = self.balance + total_pnl
