"""
Börsen-Schnittstelle für die Ausführung von Trades.
"""

import ccxt
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class ExchangeInterface:
    """
    Schnittstelle zu Kryptobörsen für die Ausführung von Orders.
    """
    
    def __init__(self, api_keys: Dict, settings: Dict):
        """
        Initialisiert die Börsen-Schnittstelle.
        
        Args:
            api_keys: API-Schlüssel für verschiedene Börsen
            settings: Einstellungen
        """
        self.api_keys = api_keys
        self.settings = settings
        self.exchanges = {}
        self.paper_trading = settings.get('paper_trading', True)
        
        # Initialisiere Börsenverbindungen
        self._initialize_exchanges()
        
        logger.info(f"ExchangeInterface initialisiert (Paper Trading: {self.paper_trading})")
    
    def _initialize_exchanges(self):
        """Initialisiert Börsenverbindungen (Kraken)."""
        try:
            # Kraken initialisieren
            if 'kraken' in self.api_keys:
                kraken_config = {
                    'enableRateLimit': True,
                    'options': {
                        'adjustForTimeDifference': True,
                    }
                }
                
                # Füge API-Keys nur hinzu wenn nicht im Paper-Trading-Modus und Keys gültig
                if not self.paper_trading:
                    api_key = self.api_keys['kraken'].get('api_key', '')
                    api_secret = self.api_keys['kraken'].get('api_secret', '')
                    if api_key and 'YOUR_KRAKEN' not in api_key:
                        kraken_config['apiKey'] = api_key
                        kraken_config['secret'] = api_secret
                
                self.exchanges['kraken'] = ccxt.kraken(kraken_config)
                logger.info("Kraken Exchange erfolgreich initialisiert")
            
        except Exception as e:
            logger.error(f"Fehler beim Initialisieren von Kraken: {str(e)}")
    
    def create_order(
        self,
        symbol: str,
        side: str,
        type: str = 'market',
        amount: float = None,
        price: float = None,
        params: Dict = None,
        exchange_id: str = 'kraken'
    ) -> Dict:
        """
        Erstellt eine Order.
        
        Args:
            symbol: Handelspaar (z.B. 'BTC/USDT')
            side: 'buy' oder 'sell'
            type: Order-Typ ('market', 'limit')
            amount: Menge
            price: Preis (nur für Limit-Orders)
            params: Zusätzliche Parameter (z.B. stopLoss, takeProfit)
            exchange_id: Börsen-ID
            
        Returns:
            Order-Informationen
        """
        if self.paper_trading:
            return self._simulate_order(symbol, side, type, amount, price, params)
        
        try:
            exchange = self.exchanges.get(exchange_id)
            if not exchange:
                raise ValueError(f"Börse '{exchange_id}' nicht verfügbar")
            
            # Erstelle Order
            if type == 'market':
                order = exchange.create_market_order(symbol, side, amount, params)
            elif type == 'limit':
                order = exchange.create_limit_order(symbol, side, amount, price, params)
            else:
                raise ValueError(f"Unbekannter Order-Typ: {type}")
            
            logger.info(f"Order erstellt: {order}")
            return order
            
        except Exception as e:
            logger.error(f"Fehler beim Erstellen der Order: {str(e)}")
            return {
                'status': 'failed',
                'error': str(e)
            }
    
    def _simulate_order(
        self,
        symbol: str,
        side: str,
        type: str,
        amount: float,
        price: float = None,
        params: Dict = None
    ) -> Dict:
        """
        Simuliert eine Order im Paper-Trading-Modus.
        
        Args:
            symbol: Handelspaar
            side: 'buy' oder 'sell'
            type: Order-Typ
            amount: Menge
            price: Preis
            params: Zusätzliche Parameter
            
        Returns:
            Simulierte Order-Informationen
        """
        import uuid
        from datetime import datetime
        
        # Simuliere Order
        simulated_order = {
            'id': str(uuid.uuid4()),
            'symbol': symbol,
            'type': type,
            'side': side,
            'amount': amount,
            'price': price if price else self._get_current_price(symbol),
            'cost': (price if price else self._get_current_price(symbol)) * amount,
            'status': 'closed',
            'timestamp': datetime.utcnow().isoformat(),
            'fee': {
                'cost': 0.001 * amount * (price if price else self._get_current_price(symbol)),
                'currency': 'USDT'
            },
            'params': params,
            'info': 'Simulated order (Paper Trading)'
        }
        
        logger.info(f"[PAPER TRADING] Order simuliert: {side.upper()} {amount} {symbol} @ {simulated_order['price']:.2f}")
        
        return simulated_order
    
    def _get_current_price(self, symbol: str, exchange_id: str = 'kraken') -> float:
        """
        Ruft den aktuellen Marktpreis ab.
        
        Args:
            symbol: Handelspaar
            exchange_id: Börsen-ID
            
        Returns:
            Aktueller Preis
        """
        try:
            exchange = self.exchanges.get(exchange_id)
            if exchange:
                ticker = exchange.fetch_ticker(symbol)
                return ticker['last']
        except Exception as e:
            logger.warning(f"Fehler beim Abrufen des Preises: {str(e)}")
        
        # Fallback: Return einen Dummy-Wert
        return 50000.0 if 'BTC' in symbol else 3000.0
    
    def get_balance(self, exchange_id: str = 'kraken') -> Dict:
        """
        Ruft den aktuellen Kontostand ab.
        
        Args:
            exchange_id: Börsen-ID
            
        Returns:
            Kontostand-Informationen
        """
        if self.paper_trading:
            return {
                'USDT': {
                    'free': 10000.0,
                    'used': 0.0,
                    'total': 10000.0
                }
            }
        
        try:
            exchange = self.exchanges.get(exchange_id)
            if exchange:
                balance = exchange.fetch_balance()
                return balance
        except Exception as e:
            logger.error(f"Fehler beim Abrufen des Kontostands: {str(e)}")
        
        return {}
    
    def get_open_orders(self, symbol: str = None, exchange_id: str = 'kraken') -> List[Dict]:
        """
        Ruft offene Orders ab.
        
        Args:
            symbol: Optional - Handelspaar
            exchange_id: Börsen-ID
            
        Returns:
            Liste offener Orders
        """
        if self.paper_trading:
            return []
        
        try:
            exchange = self.exchanges.get(exchange_id)
            if exchange:
                return exchange.fetch_open_orders(symbol)
        except Exception as e:
            logger.error(f"Fehler beim Abrufen offener Orders: {str(e)}")
        
        return []
    
    def cancel_order(self, order_id: str, symbol: str, exchange_id: str = 'kraken') -> bool:
        """
        Storniert eine Order.
        
        Args:
            order_id: Order-ID
            symbol: Handelspaar
            exchange_id: Börsen-ID
            
        Returns:
            True bei Erfolg
        """
        if self.paper_trading:
            logger.info(f"[PAPER TRADING] Order storniert: {order_id}")
            return True
        
        try:
            exchange = self.exchanges.get(exchange_id)
            if exchange:
                exchange.cancel_order(order_id, symbol)
                return True
        except Exception as e:
            logger.error(f"Fehler beim Stornieren der Order: {str(e)}")
        
        return False
