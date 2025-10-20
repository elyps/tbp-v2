"""
Datenbeschaffungsmodul für den Trading-Bot.
Stellt Funktionen zum Abrufen und Verwalten von Marktdaten bereit.
"""

import os
import time
import pandas as pd
import ccxt
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
import logging

logger = logging.getLogger(__name__)

class DataProvider:
    """
    Klasse zum Verwalten des Datenabrufs von verschiedenen Börsen und APIs.
    """
    
    def __init__(self, api_keys: Dict, settings: Dict):
        """
        Initialisiert den DataProvider.
        
        Args:
            api_keys: Dictionary mit API-Schlüsseln für verschiedene Börsen
            settings: Dictionary mit Einstellungen für den Datenabruf
        """
        self.api_keys = api_keys
        self.settings = settings
        self.exchanges = {}
        self._initialize_exchanges()
    
    def _initialize_exchanges(self):
        """Initialisiert die Börsenverbindungen (Kraken)."""
        try:
            # Kraken initialisieren (mit oder ohne API-Keys für öffentliche Daten)
            kraken_config = {
                'enableRateLimit': True,
                'options': {
                    'adjustForTimeDifference': True,
                }
            }
            
            # Füge API-Keys hinzu wenn vorhanden und gültig
            if 'kraken' in self.api_keys:
                api_key = self.api_keys['kraken'].get('api_key', '')
                api_secret = self.api_keys['kraken'].get('api_secret', '')
                
                # Nur echte Keys hinzufügen (nicht Platzhalter)
                if api_key and api_secret and 'YOUR_KRAKEN' not in api_key:
                    kraken_config['apiKey'] = api_key
                    kraken_config['secret'] = api_secret
                    logger.info("Kraken Exchange mit API-Keys initialisiert")
                else:
                    logger.info("Kraken Exchange ohne API-Keys initialisiert (nur öffentliche Daten)")
            
            self.exchanges['kraken'] = ccxt.kraken(kraken_config)
            logger.info("Kraken Exchange erfolgreich initialisiert")
            
            # Standard-Exchange auf Kraken setzen
            self.default_exchange = self.exchanges.get('kraken')
            
        except Exception as e:
            logger.error(f"Fehler beim Initialisieren von Kraken: {str(e)}")
            raise
    
    def get_historical_data(
        self, 
        symbol: str, 
        timeframe: str = '1d', 
        limit: int = 1000,
        since: Optional[Union[int, str, datetime]] = None,
        exchange_id: str = None
    ) -> Optional[pd.DataFrame]:
        """
        Ruft historische Kursdaten für das angegebene Symbol ab.
        
        Args:
            symbol: Handelsymbol (z.B. 'BTC/USDT')
            timeframe: Zeitrahmen der Kerzen (z.B. '1m', '5m', '1h', '1d')
            limit: Maximale Anzahl der abzurufenden Kerzen
            since: Startzeitpunkt als Unix-Timestamp (ms), ISO-String oder datetime-Objekt
            exchange_id: ID der zu verwendenden Börse (falls nicht angegeben, wird die Standardbörse verwendet)
            
        Returns:
            DataFrame mit den historischen Daten oder None bei einem Fehler
        """
        exchange = self.exchanges.get(exchange_id) if exchange_id else self.default_exchange
        if not exchange:
            logger.error("Keine gültige Börse konfiguriert")
            return None
        
        try:
            # since in das richtige Format umwandeln
            if isinstance(since, str):
                since = int(pd.Timestamp(since).timestamp() * 1000)
            elif isinstance(since, datetime):
                since = int(since.timestamp() * 1000)
            
            logger.info(f"Hole historische Daten für {symbol} ({timeframe}), Limit: {limit}" + 
                       (f" ab {pd.to_datetime(since/1000, unit='s')}" if since else ""))
            
            # OHLCV-Daten abrufen
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=limit)
            
            if not ohlcv:
                logger.warning(f"Keine Daten für {symbol} erhalten")
                return None
            
            # In DataFrame umwandeln
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            # Datentypen konvertieren
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col])
            
            logger.info(f"Erfolgreich {len(df)} Kerzen für {symbol} geladen")
            return df
            
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der historischen Daten für {symbol}: {str(e)}")
            return None
    
    def get_current_price(self, symbol: str, exchange_id: str = None) -> Optional[float]:
        """
        Ruft den aktuellen Preis für ein Symbol ab.
        
        Args:
            symbol: Handelsymbol (z.B. 'BTC/USDT')
            exchange_id: ID der zu verwendenden Börse
            
        Returns:
            Aktueller Preis oder None bei einem Fehler
        """
        exchange = self.exchanges.get(exchange_id) if exchange_id else self.default_exchange
        if not exchange:
            logger.error("Keine gültige Börse konfiguriert")
            return None
        
        try:
            ticker = exchange.fetch_ticker(symbol)
            return float(ticker['last'])
        except Exception as e:
            logger.error(f"Fehler beim Abrufen des aktuellen Preises für {symbol}: {str(e)}")
            return None
    
    def get_order_book(self, symbol: str, limit: int = 20, exchange_id: str = None) -> Optional[Dict]:
        """
        Ruft das Orderbuch für ein Symbol ab.
        
        Args:
            symbol: Handelsymbol (z.B. 'BTC/USDT')
            limit: Maximale Anzahl der Orderbuch-Einträge pro Seite
            exchange_id: ID der zu verwendenden Börse
            
        Returns:
            Dictionary mit 'bids' und 'asks' oder None bei einem Fehler
        """
        exchange = self.exchanges.get(exchange_id) if exchange_id else self.default_exchange
        if not exchange:
            logger.error("Keine gültige Börse konfiguriert")
            return None
        
        try:
            return exchange.fetch_order_book(symbol, limit=limit)
        except Exception as e:
            logger.error(f"Fehler beim Abrufen des Orderbuchs für {symbol}: {str(e)}")
            return None
    
    def get_recent_trades(self, symbol: str, limit: int = 100, exchange_id: str = None) -> Optional[pd.DataFrame]:
        """
        Ruft die letzten Trades für ein Symbol ab.
        
        Args:
            symbol: Handelsymbol (z.B. 'BTC/USDT')
            limit: Maximale Anzahl der abzurufenden Trades
            exchange_id: ID der zu verwendenden Börse
            
        Returns:
            DataFrame mit den letzten Trades oder None bei einem Fehler
        """
        exchange = self.exchanges.get(exchange_id) if exchange_id else self.default_exchange
        if not exchange:
            logger.error("Keine gültige Börse konfiguriert")
            return None
        
        try:
            trades = exchange.fetch_trades(symbol, limit=limit)
            if not trades:
                return None
                
            df = pd.DataFrame(trades, columns=['timestamp', 'symbol', 'side', 'price', 'amount', 'cost', 'id'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            # Datentypen konvertieren
            for col in ['price', 'amount', 'cost']:
                df[col] = pd.to_numeric(df[col])
                
            return df
            
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Trades für {symbol}: {str(e)}")
            return None
    
    def get_funding_rate_history(
        self, 
        symbol: str, 
        since: Optional[Union[int, str, datetime]] = None,
        limit: int = 100,
        exchange_id: str = None
    ) -> Optional[pd.DataFrame]:
        """
        Ruft den Verlauf der Funding Rates für ein Perpetual-Future-Paar ab.
        
        Args:
            symbol: Handelsymbol (z.B. 'BTC/USDT:USDT')
            since: Startzeitpunkt als Unix-Timestamp (ms), ISO-String oder datetime-Objekt
            limit: Maximale Anzahl der abzurufenden Einträge
            exchange_id: ID der zu verwendenden Börse
            
        Returns:
            DataFrame mit dem Funding-Rate-Verlauf oder None bei einem Fehler
        """
        exchange = self.exchanges.get(exchange_id) if exchange_id else self.default_exchange
        if not exchange:
            logger.error("Keine gültige Börse konfiguriert")
            return None
        
        try:
            # since in das richtige Format umwandeln
            if isinstance(since, str):
                since = int(pd.Timestamp(since).timestamp() * 1000)
            elif isinstance(since, datetime):
                since = int(since.timestamp() * 1000)
            
            # Prüfen, ob die Börse Funding Rates unterstützt
            if not hasattr(exchange, 'fetch_funding_rate_history'):
                logger.warning(f"Die Börse {exchange_id} unterstützt keine Funding-Rate-Abfragen")
                return None
            
            funding_rates = exchange.fetch_funding_rate_history(symbol, since=since, limit=limit)
            
            if not funding_rates:
                return None
            
            # In DataFrame umwandeln
            df = pd.DataFrame(funding_rates)
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            return df
            
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Funding Rates für {symbol}: {str(e)}")
            return None


# Hilfsfunktion zum Testen des Moduls
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Beispielverwendung
    api_keys = {
        'binance': {
            'api_key': 'YOUR_API_KEY',
            'api_secret': 'YOUR_API_SECRET'
        }
    }
    
    dp = DataProvider(api_keys=api_keys, settings={})
    
    # Historische Daten abrufen
    df = dp.get_historical_data('BTC/USDT', '1d', limit=30)
    if df is not None:
        print("\nLetzte 5 Einträge der historischen Daten:")
        print(df.tail())
    
    # Aktuellen Preis abrufen
    price = dp.get_current_price('BTC/USDT')
    if price is not None:
        print(f"\nAktueller BTC/USDT Preis: {price:.2f}")
    
    # Orderbuch abrufen
    orderbook = dp.get_order_book('BTC/USDT', limit=5)
    if orderbook:
        print("\nOrderbuch (erste 5 Einträge):")
        print("Bids (Kauf):", orderbook['bids'][:5])
        print("Asks (Verkauf):", orderbook['asks'][:5])
