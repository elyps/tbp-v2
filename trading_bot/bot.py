"""
Hauptmodul des Trading-Bots
"""

import logging
import json
import time
import uuid
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union

# Interne Importe
from .data_provider import DataProvider
from .indicators import TechnicalIndicators
from .ml_model import MLModel
from .strategy import StrategyManager
from .risk_management import RiskManager
from .exchange import ExchangeInterface
from .utils import setup_logging
from .config import (
    API_KEYS, DEFAULT_SETTINGS, INDICATORS, ML_SETTINGS, 
    RISK_MANAGEMENT, STRATEGIES, LOGGING_CONFIG
)

# Logger einrichten
setup_logging(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

class TradingBot:
    """
    Hauptklasse des Trading-Bots, die alle Komponenten koordiniert.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialisiert den Trading-Bot mit der angegebenen Konfiguration.
        
        Args:
            config: Optionale Konfiguration, die die Standardwerte überschreibt
        """
        self.config = self._load_config(config)
        self._initialize_components()
        self.is_running = False
        self.portfolio = self._initialize_portfolio()
        
        logger.info("Trading-Bot erfolgreich initialisiert")
    
    def _load_config(self, config: Optional[Dict]) -> Dict:
        """Lädt die Konfiguration und führt sie mit den Standardwerten zusammen."""
        if config is None:
            config = {}
            
        # Standardkonfiguration mit übergebenen Werten überschreiben
        merged_config = {
            'api_keys': {**API_KEYS, **(config.get('api_keys', {}))},
            'settings': {**DEFAULT_SETTINGS, **(config.get('settings', {}))},
            'indicators': {**INDICATORS, **(config.get('indicators', {}))},
            'ml_settings': {**ML_SETTINGS, **(config.get('ml_settings', {}))},
            'risk_management': {**RISK_MANAGEMENT, **(config.get('risk_management', {}))},
            'strategies': {**STRATEGIES, **(config.get('strategies', {}))},
        }
        
        return merged_config
    
    def _initialize_components(self):
        """Initialisiert alle Komponenten des Bots."""
        logger.info("Initialisiere Bot-Komponenten...")
        
        # Datenprovider initialisieren
        self.data_provider = DataProvider(
            api_keys=self.config['api_keys'],
            settings=self.config['settings']
        )
        
        # Technische Indikatoren initialisieren
        self.indicators = TechnicalIndicators(
            config=self.config['indicators']
        )
        
        # KI-Modell initialisieren
        self.ml_model = MLModel(
            settings=self.config['ml_settings']
        )
        
        # Strategie-Manager initialisieren
        self.strategy_manager = StrategyManager(
            strategies_config=self.config['strategies'],
            indicators=self.indicators,
            ml_model=self.ml_model
        )
        
        # Risikomanager initialisieren
        self.risk_manager = RiskManager(
            config=self.config['risk_management'],
            initial_balance=self.config['settings']['initial_balance']
        )
        
        # Börsenschnittstelle initialisieren
        self.exchange = ExchangeInterface(
            api_keys=self.config['api_keys'],
            settings=self.config['settings']
        )
        
        logger.info("Alle Komponenten erfolgreich initialisiert")
    
    def _initialize_portfolio(self) -> Dict:
        """Initialisiert das Portfolio mit dem Startkapital."""
        return {
            'balance': self.config['settings']['initial_balance'],
            'equity': self.config['settings']['initial_balance'],
            'positions': {},
            'trades': [],
            'performance': {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0.0,
                'profit_factor': 0.0,
                'max_drawdown': 0.0,
                'sharpe_ratio': 0.0,
            },
            'last_updated': datetime.utcnow().isoformat()
        }
    
    def run(self, symbols: List[str] = None):
        """
        Startet den Trading-Bot.
        
        Args:
            symbols: Liste der zu handelnden Symbole (z.B. ['BTC/USDT', 'ETH/USDT'])
        """
        if symbols is None:
            symbols = ['BTC/USDT']  # Standardwert
            
        self.is_running = True
        logger.info(f"Starte Trading-Bot für Symbole: {', '.join(symbols)}")
        
        try:
            while self.is_running:
                for symbol in symbols:
                    self._process_symbol(symbol)
                
                # Kurze Pause, um die API nicht zu überlasten
                time.sleep(60)  # 1 Minute Pause zwischen den Zyklen
                
        except KeyboardInterrupt:
            logger.info("Trading-Bot wird beendet...")
        except Exception as e:
            logger.error(f"Fehler im Hauptloop: {str(e)}", exc_info=True)
        finally:
            self.stop()
    
    def _process_symbol(self, symbol: str):
        """
        Verarbeitet ein einzelnes Symbol.
        
        Args:
            symbol: Das zu verarbeitende Symbol (z.B. 'BTC/USDT')
        """
        try:
            # 1. Marktdaten abrufen
            df = self.data_provider.get_historical_data(
                symbol=symbol,
                timeframe=self.config['settings']['timeframe'],
                limit=1000  # Anzahl der Kerzen
            )
            
            if df is None or df.empty:
                logger.warning(f"Keine Daten für {symbol} erhalten")
                return
            
            # 2. Technische Indikatoren berechnen
            df_with_indicators = self.indicators.calculate_all(df)
            
            # 3. KI-Modell für Vorhersagen nutzen
            predictions = self.ml_model.predict(df_with_indicators)
            
            # 4. Strategien auswerten
            signals = self.strategy_manager.evaluate(
                df=df_with_indicators,
                predictions=predictions,
                symbol=symbol
            )
            
            if signals:
                logger.info(f"{len(signals)} Handelssignal(e) für {symbol} generiert")
                for i, sig in enumerate(signals, 1):
                    logger.info(f"  Signal {i}: {sig['action'].upper()} - {sig['strategy']} - Konfidenz: {sig['confidence']:.1%} - {sig['reason']}")
            else:
                logger.debug(f"Keine Handelssignale für {symbol}")
            
            # 5. Risikomanagement anwenden
            trade_decisions = self.risk_manager.evaluate_risk(
                signals=signals,
                portfolio=self.portfolio,
                current_price=df_with_indicators['close'].iloc[-1]
            )
            
            if trade_decisions:
                logger.info(f"{len(trade_decisions)} Handelsentscheidung(en) nach Risikomanagement")
            elif signals:
                logger.info(f"Alle Signale vom Risikomanagement abgelehnt")
            
            # 6. Trades ausführen
            self._execute_trades(trade_decisions, symbol)
            
            # 7. Portfolio aktualisieren
            self._update_portfolio()
            
            logger.info(f"Verarbeitung für {symbol} abgeschlossen")
            
        except Exception as e:
            logger.error(f"Fehler bei der Verarbeitung von {symbol}: {str(e)}", exc_info=True)
    
    def _execute_trades(self, trade_decisions: List[Dict], symbol: str):
        """
        Führt die Handelsentscheidungen aus.
        
        Args:
            trade_decisions: Liste von Handelsentscheidungen
            symbol: Das gehandelte Symbol
        """
        if not trade_decisions:
            return
            
        for decision in trade_decisions:
            try:
                if decision['action'] == 'buy':
                    order = self.exchange.create_order(
                        symbol=symbol,
                        side='buy',
                        type=decision.get('order_type', 'market'),
                        amount=decision['amount'],
                        price=decision.get('price'),
                        params={
                            'stopLoss': decision.get('stop_loss'),
                            'takeProfit': decision.get('take_profit')
                        }
                    )
                    logger.info(f"Kauforder ausgeführt: {order}")
                    
                elif decision['action'] == 'sell':
                    order = self.exchange.create_order(
                        symbol=symbol,
                        side='sell',
                        type=decision.get('order_type', 'market'),
                        amount=decision['amount'],
                        price=decision.get('price')
                    )
                    logger.info(f"Verkaufsorder ausgeführt: {order}")
                
                # Trade-Informationen speichern
                self._record_trade(decision, order)
                
            except Exception as e:
                logger.error(f"Fehler beim Ausführen des Trades: {str(e)}", exc_info=True)
    
    def _record_trade(self, decision: Dict, order: Dict):
        """
        Speichert die Handelsinformationen und aktualisiert Portfolio.
        
        Args:
            decision: Die Handelsentscheidung
            order: Die ausgeführte Order
        """
        symbol = order.get('symbol')
        side = decision['action']
        amount = decision['amount']
        price = order.get('price')
        cost = order.get('cost', amount * price)
        fee_info = order.get('fee', {})
        fee = fee_info.get('cost', cost * 0.001) if isinstance(fee_info, dict) else 0
        
        trade = {
            'id': order.get('id', str(uuid.uuid4())),
            'symbol': symbol,
            'side': side,
            'amount': amount,
            'price': price,
            'cost': cost,
            'fee': fee,
            'timestamp': datetime.utcnow().isoformat(),
            'status': order.get('status', 'closed'),
            'stop_loss': decision.get('stop_loss'),
            'take_profit': decision.get('take_profit'),
            'strategy': decision.get('strategy', 'unknown'),
            'risk_reward_ratio': decision.get('risk_reward_ratio'),
            'pnl': 0  # Wird beim Schließen berechnet
        }
        
        # Portfolio aktualisieren basierend auf Trade-Richtung
        if side == 'buy':
            self._execute_buy(symbol, amount, price, cost, fee, trade)
        elif side == 'sell':
            self._execute_sell(symbol, amount, price, cost, fee, trade)
        
        self.portfolio['trades'].append(trade)
        
        # Portfolio-Statistiken aktualisieren
        self._update_portfolio_stats(trade)
        
        logger.info(f"Trade aufgezeichnet: {side.upper()} {amount:.6f} {symbol} @ {price:.2f}")
    
    def _execute_buy(self, symbol: str, amount: float, price: float, cost: float, fee: float, trade: Dict):
        """Führt einen Kauf aus und aktualisiert Portfolio."""
        total_cost = cost + fee
        
        # Prüfe ob genug Balance vorhanden
        if self.portfolio['balance'] < total_cost:
            logger.warning(f"Nicht genug Balance für Kauf: {total_cost:.2f} benötigt, {self.portfolio['balance']:.2f} verfügbar")
            return
        
        # Reduziere Balance
        self.portfolio['balance'] -= total_cost
        
        # Füge oder aktualisiere Position
        if symbol not in self.portfolio['positions']:
            self.portfolio['positions'][symbol] = {
                'amount': amount,
                'avg_price': price,
                'total_cost': total_cost,
                'side': 'long',
                'entry_time': datetime.utcnow().isoformat()
            }
        else:
            # Erhöhe bestehende Position
            pos = self.portfolio['positions'][symbol]
            new_amount = pos['amount'] + amount
            new_total_cost = pos['total_cost'] + total_cost
            pos['amount'] = new_amount
            pos['avg_price'] = new_total_cost / new_amount
            pos['total_cost'] = new_total_cost
        
        logger.info(f"Kauf ausgeführt: -{total_cost:.2f} EUR, Neue Balance: {self.portfolio['balance']:.2f} EUR")
    
    def _execute_sell(self, symbol: str, amount: float, price: float, cost: float, fee: float, trade: Dict):
        """Führt einen Verkauf aus und aktualisiert Portfolio."""
        proceeds = cost - fee
        
        # Prüfe ob Position existiert
        if symbol not in self.portfolio['positions']:
            logger.warning(f"Keine Position für {symbol} vorhanden zum Verkaufen")
            return
        
        pos = self.portfolio['positions'][symbol]
        
        # Prüfe ob genug in Position
        if pos['amount'] < amount:
            logger.warning(f"Nicht genug in Position: {amount} verkaufen, nur {pos['amount']} verfügbar")
            amount = pos['amount']
        
        # Berechne P&L
        avg_cost_per_unit = pos['avg_price']
        pnl = (price - avg_cost_per_unit) * amount - fee
        trade['pnl'] = pnl
        
        # Erhöhe Balance
        self.portfolio['balance'] += proceeds
        
        # Aktualisiere oder schließe Position
        pos['amount'] -= amount
        if pos['amount'] <= 0.0001:  # Position vollständig geschlossen
            del self.portfolio['positions'][symbol]
            logger.info(f"Position {symbol} geschlossen")
        
        logger.info(f"Verkauf ausgeführt: +{proceeds:.2f} EUR, P&L: {pnl:+.2f} EUR, Neue Balance: {self.portfolio['balance']:.2f} EUR")
    
    def _update_portfolio_stats(self, trade: Dict):
        """Aktualisiert die Portfolio-Statistiken basierend auf dem letzten Trade."""
        if trade['status'] != 'closed':
            return
        
        self.portfolio['performance']['total_trades'] += 1
        
        # Für Verkäufe: Prüfe P&L
        if trade['side'] == 'sell':
            pnl = trade.get('pnl', 0)
            if pnl > 0:
                self.portfolio['performance']['winning_trades'] += 1
            else:
                self.portfolio['performance']['losing_trades'] += 1
        
        # Win-Rate aktualisieren
        total = self.portfolio['performance']['total_trades']
        wins = self.portfolio['performance']['winning_trades']
        losses = self.portfolio['performance']['losing_trades']
        
        if wins + losses > 0:
            self.portfolio['performance']['win_rate'] = (wins / (wins + losses)) * 100
    
    def _save_portfolio_state(self):
        """Speichert den aktuellen Portfolio-Status in eine JSON-Datei."""
        try:
            with open('portfolio_state.json', 'w') as f:
                json.dump(self.portfolio, f, indent=2)
        except Exception as e:
            logger.error(f"Fehler beim Speichern des Portfolio-Status: {str(e)}")
    
    def _update_portfolio(self):
        """Aktualisiert das Portfolio mit den aktuellen Marktdaten."""
        # Hier würden wir die aktuellen Positionen und das Guthaben aktualisieren
        # Dies ist eine vereinfachte Version
        
        # Beispiel: Aktuelles Gesamtvermögen berechnen
        # In einer echten Implementierung würden wir die aktuellen Marktpreise abfragen
        total_value = self.portfolio['balance']
        
        # Wert offener Positionen hinzufügen
        for symbol, position in self.portfolio['positions'].items():
            # Hier würden wir den aktuellen Marktpreis abfragen
            current_price = self.data_provider.get_current_price(symbol)
            if current_price is not None:
                position_value = position['amount'] * current_price
                total_value += position_value
        
        self.portfolio['equity'] = total_value
        self.portfolio['last_updated'] = datetime.utcnow().isoformat()
        
        # Portfolio-Status speichern für Monitoring
        self._save_portfolio_state()
    
    def stop(self):
        """Stoppt den Trading-Bot sicher."""
        self.is_running = False
        logger.info("Trading-Bot wurde gestoppt")
    
    def get_portfolio_summary(self) -> Dict:
        """Gibt eine Zusammenfassung des aktuellen Portfolios zurück."""
        return {
            'balance': self.portfolio['balance'],
            'equity': self.portfolio['equity'],
            'open_positions': len(self.portfolio['positions']),
            'total_trades': self.portfolio['performance']['total_trades'],
            'win_rate': self.portfolio['performance']['win_rate'],
            'last_updated': self.portfolio['last_updated']
        }
    
    def get_trade_history(self, limit: int = 100) -> List[Dict]:
        """
        Gibt den Handelsverlauf zurück.
        
        Args:
            limit: Maximale Anzahl der zurückzugebenden Trades
            
        Returns:
            Liste der Trades, sortiert nach Datum (neueste zuerst)
        """
        return sorted(
            self.portfolio['trades'],
            key=lambda x: x.get('timestamp', ''),
            reverse=True
        )[:limit]


def main():
    """Hauptfunktion zum Starten des Trading-Bots."""
    # Konfiguration anpassen (optional)
    config = {
        'settings': {
            'initial_balance': 10000.0,
            'risk_per_trade': 1.0,
        },
        'strategies': {
            'trend_following': {'enabled': True},
            'mean_reversion': {'enabled': False},
            'breakout': {'enabled': True},
        },
    }
    
    # Trading-Bot initialisieren und starten
    bot = TradingBot(config=config)
    
    try:
        # Bot mit Top 5 Kraken-Paaren starten (höchste Liquidität & Marktkapitalisierung)
        # USD-Paare (beste Liquidität weltweit) + EUR-Paare (europäischer Markt)
        symbols = [
            # Top USD-Paare (beste Liquidität)
            'BTC/USD',   # Bitcoin - $1.8T Marktkappe, höchste Liquidität
            'ETH/USD',   # Ethereum - $400B Marktkappe
            'SOL/USD',   # Solana - $80B Marktkappe, schnell wachsend
            'XRP/USD',   # Ripple - $140B Marktkappe, sehr stabil
            'ADA/USD',   # Cardano - $35B Marktkappe, stabil
            # EUR-Paare für europäischen Markt
            'BTC/EUR',   # Bitcoin EUR
            'ETH/EUR',   # Ethereum EUR
        ]
        bot.run(symbols=symbols)
    except KeyboardInterrupt:
        print("\nTrading-Bot wird beendet...")
    except Exception as e:
        print(f"Ein Fehler ist aufgetreten: {str(e)}")
    finally:
        bot.stop()


if __name__ == "__main__":
    main()
