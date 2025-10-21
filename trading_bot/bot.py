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
from .continuous_learning import TrainingDataCollector, ContinuousLearner
from .database import get_database
from .config import (
    API_KEYS, DEFAULT_SETTINGS, INDICATORS, ML_SETTINGS, 
    RISK_MANAGEMENT, STRATEGIES, LOGGING_CONFIG
)

# Logger einrichten - MUSS vor den Imports stehen!
setup_logging(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

# Neue Enhanced Pipeline (Companion Codex)
try:
    import sys
    from pathlib import Path
    # Füge trader-Pfad hinzu
    trader_path = Path(__file__).parent.parent / "trader"
    if str(trader_path) not in sys.path:
        sys.path.insert(0, str(trader_path))
    
    from trader.data.features import add_features
    from trader.signals.trend_meta import TrendMeta
    from trader.sizing.vol_sizer import VolSizer
    from trader.risk.rules import RiskParams, compute_stop
    from trader.live.execution import ExecutionEngine
    from trader.live.broker import PaperBroker
    from trader.utils.config import load_cfg
    
    ENHANCED_PIPELINE_AVAILABLE = True
    logger.info("Enhanced Pipeline (Companion Codex) verfügbar")
except ImportError as e:
    ENHANCED_PIPELINE_AVAILABLE = False
    logger.warning(f"Enhanced Pipeline nicht verfügbar: {e}")

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
        
        # Kontinuierliches Lernsystem initialisieren
        self.continuous_learning_enabled = self.config['settings'].get('continuous_learning', True)
        if self.continuous_learning_enabled:
            self._initialize_continuous_learning()
        else:
            logger.info("Kontinuierliches Lernen deaktiviert")
        
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
        
        # SQLite Datenbank initialisieren
        self.db = get_database('trading_bot.db')
        logger.info("✓ SQLite Datenbank verbunden")
        
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
        
        # Enhanced Pipeline (Companion Codex) initialisieren falls verfügbar und aktiviert
        self.use_enhanced_pipeline = self.config['settings'].get('use_enhanced_pipeline', False)
        if self.use_enhanced_pipeline and ENHANCED_PIPELINE_AVAILABLE:
            logger.info("Initialisiere Enhanced Pipeline (Companion Codex)...")
            self._initialize_enhanced_pipeline()
        elif self.use_enhanced_pipeline and not ENHANCED_PIPELINE_AVAILABLE:
            logger.warning("Enhanced Pipeline aktiviert aber nicht verfügbar - verwende Legacy Pipeline")
            self.use_enhanced_pipeline = False
        
        logger.info("Alle Komponenten erfolgreich initialisiert")
    
    def _initialize_continuous_learning(self):
        """Initialisiert das kontinuierliche Lernsystem."""
        try:
            logger.info("Initialisiere Kontinuierliches Lernsystem...")
            
            # Datensammler
            self.data_collector = TrainingDataCollector(
                data_dir=self.config['settings'].get('training_data_dir', 'training_data')
            )
            
            # Continuous Learner
            learning_config = {
                'min_samples_for_retrain': self.config['settings'].get('min_samples_retrain', 100),
                'retrain_frequency_hours': self.config['settings'].get('retrain_frequency_hours', 24),
                'model_versions_dir': 'models/versions'
            }
            
            self.continuous_learner = ContinuousLearner(
                ml_model=self.ml_model,
                data_collector=self.data_collector,
                config=learning_config
            )
            
            # Tracking für offene Trades (um Outcomes zu sammeln)
            self.open_trades_tracking = {}  # {trade_id: {trade_info, features, entry_time}}
            
            logger.info("✓ Kontinuierliches Lernsystem aktiviert")
            
        except Exception as e:
            logger.error(f"Fehler bei Initialisierung des Continuous Learning: {e}")
            self.continuous_learning_enabled = False
    
    def _initialize_enhanced_pipeline(self):
        """Initialisiert die Enhanced Pipeline Komponenten."""
        try:
            # Lade trader Konfiguration
            trader_config_path = Path(__file__).parent.parent / "trader" / "config.yaml"
            if trader_config_path.exists():
                self.trader_config = load_cfg(str(trader_config_path))
                logger.info("Trader Konfiguration geladen")
            else:
                logger.warning("Trader config.yaml nicht gefunden, verwende Defaults")
                self.trader_config = None
            
            # Initialisiere Signal-Modell (wird später trainiert)
            self.trend_meta_model = TrendMeta(
                p_up=self.trader_config.signals.p_up if self.trader_config else 0.55,
                p_dn=self.trader_config.signals.p_dn if self.trader_config else 0.55,
                allow_short=self.trader_config.signals.allow_short if self.trader_config else False,
            )
            
            # Initialisiere Position Sizer
            self.vol_sizer = VolSizer(
                target_vol=self.trader_config.sizing.target_vol if self.trader_config else 0.10,
                cap=self.trader_config.sizing.cap if self.trader_config else 0.03,
            )
            
            # Initialisiere Risk Parameter
            self.risk_params = RiskParams(
                max_pos_per_asset=self.trader_config.risk.max_pos_per_asset if self.trader_config else 0.03,
                max_gross=self.trader_config.risk.max_gross if self.trader_config else 0.6,
                stop_atr_mult=self.trader_config.risk.stop_atr_mult if self.trader_config else 2.0,
                trail_atr_mult=self.trader_config.risk.trail_atr_mult if self.trader_config else 3.0,
                day_dd_kill=self.trader_config.risk.day_dd_kill if self.trader_config else 0.08,
            )
            
            # Paper Broker für Simulation (falls nicht live)
            if self.config['settings'].get('paper_trading', True):
                self.paper_broker = PaperBroker(
                    initial_balance=self.config['settings']['initial_balance']
                )
                self.execution_engine = ExecutionEngine(
                    broker=self.paper_broker,
                    sizer=self.vol_sizer,
                    risk=self.risk_params,
                    contract_size=1.0
                )
            
            logger.info("Enhanced Pipeline erfolgreich initialisiert")
            
        except Exception as e:
            logger.error(f"Fehler bei Initialisierung der Enhanced Pipeline: {e}")
            self.use_enhanced_pipeline = False
    
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
        """Startet den Trading-Bot."""
        if symbols is None:
            symbols = ['BTC/USDT']

        self.is_running = True
        logger.info(f"Starte Trading-Bot für Symbole: {', '.join(symbols)}")

        try:
            while self.is_running:
                for symbol in symbols:
                    self._process_symbol(symbol)

                time.sleep(60)

        except KeyboardInterrupt:
            logger.info("Trading-Bot wird beendet...")
        except Exception as e:
            logger.error(f"Fehler im Hauptloop: {str(e)}", exc_info=True)
        finally:
            self.stop()

    def _process_symbol(self, symbol: str):
        """Verarbeitet ein einzelnes Symbol."""
        logger.debug(f"[Core] Verarbeite Symbol {symbol} (Enhanced={self.use_enhanced_pipeline})")
        try:
            if self.use_enhanced_pipeline:
                self._process_symbol_enhanced(symbol)
            else:
                self._process_symbol_legacy(symbol)
        except Exception as e:
            logger.error(f"Fehler bei der Verarbeitung von {symbol}: {str(e)}", exc_info=True)

    def _process_symbol_legacy(self, symbol: str):
        """Verarbeitet ein Symbol mit der Legacy Pipeline."""
        logger.debug(f"[Legacy] Starte Verarbeitung für {symbol}")
        df = self.data_provider.get_historical_data(
            symbol=symbol,
            timeframe=self.config['settings']['timeframe'],
            limit=1000
        )

        if df is None or df.empty:
            logger.warning(f"Keine Daten für {symbol} erhalten")
            return
        logger.debug(f"[Legacy] Marktdaten erhalten: {len(df)} Kerzen")

        df_with_indicators = self.indicators.calculate_all(df)
        logger.debug(f"[Legacy] Indikator-Spalten: {list(df_with_indicators.columns)}")

        predictions = self.ml_model.predict(df_with_indicators)
        logger.debug(f"[Legacy] ML-Vorhersage: {predictions}")

        signals = self.strategy_manager.evaluate(
            df=df_with_indicators,
            predictions=predictions,
            symbol=symbol
        )

        if signals:
            logger.info(f"{len(signals)} Handelssignal(e) für {symbol} generiert")
            for idx, sig in enumerate(signals, 1):
                logger.info(
                    "  Signal %d: %s - %s - Konfidenz: %.1f%% - %s",
                    idx,
                    sig['action'].upper(),
                    sig['strategy'],
                    sig['confidence'] * 100,
                    sig['reason'],
                )
                logger.debug(f"[Legacy] Signal {idx} Details: {sig}")
        else:
            logger.debug(f"[Legacy] Keine Handelssignale für {symbol}")

        exit_signals = self._check_position_exits(symbol, df_with_indicators['close'].iloc[-1])
        if exit_signals:
            logger.debug(f"[Legacy] Exit-Signale: {exit_signals}")

        trade_decisions = self.risk_manager.evaluate_risk(
            signals=signals + exit_signals,
            portfolio=self.portfolio,
            current_price=df_with_indicators['close'].iloc[-1],
            market_data=df_with_indicators
        )

        if trade_decisions:
            logger.info(f"{len(trade_decisions)} Handelsentscheidung(en) nach Risikomanagement")
            logger.debug(f"[Legacy] Entscheidungen: {trade_decisions}")
        elif signals:
            logger.info("Alle Signale vom Risikomanagement abgelehnt")

        self._execute_trades(trade_decisions, symbol, df_with_indicators)

        logger.debug(f"[Legacy] Portfolio-Update für {symbol}")
        self._update_portfolio()

        if self.continuous_learning_enabled:
            logger.debug("[Legacy] Prüfe Continuous Learning")
            self._check_and_retrain()

        logger.info(f"Verarbeitung für {symbol} abgeschlossen (Legacy Pipeline)")

    def _process_symbol_enhanced(self, symbol: str):
        """Verarbeitet ein Symbol mit der Enhanced Pipeline."""
        try:
            logger.debug(f"[Enhanced] Starte Verarbeitung für {symbol}")
            df = self.data_provider.get_historical_data(
                symbol=symbol,
                timeframe=self.config['settings']['timeframe'],
                limit=1000
            )

            if df is None or df.empty:
                logger.warning(f"Keine Daten für {symbol} erhalten")
                return
            logger.debug(f"[Enhanced] Marktdaten erhalten: {len(df)} Kerzen")

            df_features = add_features(df.copy())
            logger.debug(f"[Enhanced] Feature-Spalten: {list(df_features.columns)}")

            if not hasattr(self, '_enhanced_model_trained') or not self._enhanced_model_trained.get(symbol, False):
                logger.debug(f"[Enhanced] Trainiere Modell für {symbol}")
                self._train_enhanced_model(df_features, symbol)

            current_data = df_features.iloc[-1:]
            side_series = self.trend_meta_model.predict_side(current_data)
            conf_series = self.trend_meta_model.predict_conf(current_data)
            current_side = side_series.iloc[-1] if not side_series.empty else "flat"
            current_conf = conf_series.iloc[-1] if not conf_series.empty else 0.0
            logger.debug(f"[Enhanced] Roh-Signal: side={current_side}, conf={current_conf:.2f}")

            if current_side != "flat":
                logger.info(f"Enhanced Signal für {symbol}: {current_side.upper()} - Konfidenz: {current_conf:.1%}")
                atr = df_features['atr'].iloc[-1] if 'atr' in df_features.columns else 0.01
                target_fraction = self.vol_sizer.size_fraction(current_data.iloc[-1:], current_conf, atr)
                target_fraction = min(target_fraction, self.risk_params.max_pos_per_asset)
                logger.debug(
                    "[Enhanced] Positionsgröße: fraction=%.4f, atr=%.5f",
                    target_fraction,
                    atr,
                )

                if self.config['settings'].get('paper_trading', True) and hasattr(self, 'execution_engine'):
                    signals = self._convert_enhanced_to_legacy_signals(
                        symbol, current_side, current_conf, target_fraction, df_features.iloc[-1]
                    )
                    logger.debug(f"[Enhanced] Konvertierte Signale: {signals}")
                    trade_decisions = self.risk_manager.evaluate_risk(
                        signals=signals,
                        portfolio=self.portfolio,
                        current_price=df_features['close'].iloc[-1]
                    )
                    logger.debug(f"[Enhanced] Entscheidungen: {trade_decisions}")
                    self._execute_trades(trade_decisions, symbol, df_features)
                else:
                    logger.info("Live Trading nicht implementiert für Enhanced Pipeline")
            else:
                logger.debug(f"Keine Enhanced Signale für {symbol}")

            logger.debug(f"[Enhanced] Portfolio-Update für {symbol}")
            self._update_portfolio()

            if self.continuous_learning_enabled:
                logger.debug("[Enhanced] Prüfe Continuous Learning")
                self._check_and_retrain()

            logger.info(f"Verarbeitung für {symbol} abgeschlossen (Enhanced Pipeline)")

        except Exception as e:
            logger.error(f"Fehler in Enhanced Pipeline für {symbol}: {str(e)}", exc_info=True)
            logger.info(f"Fallback auf Legacy Pipeline für {symbol}")
            self._process_symbol_legacy(symbol)

    def _execute_trades(self, trade_decisions: List[Dict], symbol: str, market_data: pd.DataFrame = None):
        """Führt Handelsentscheidungen aus und protokolliert jeden Schritt."""
        if not trade_decisions:
            logger.debug("Keine Handelsentscheidungen auszuführen")
            return

        for decision in trade_decisions:
            try:
                logger.debug(f"[Trade] Entscheidung empfangen: {decision}")
                action = decision.get('action')
                if action == 'buy':
                    order = self.exchange.create_order(
                        symbol=symbol,
                        side='buy',
                        type=decision.get('order_type', 'market'),
                        amount=decision['amount'],
                        price=decision.get('price'),
                        params={'stopLoss': decision.get('stop_loss'), 'takeProfit': decision.get('take_profit')}
                    )
                    logger.info(f"Kauforder ausgeführt: {order}")
                elif action == 'sell':
                    order = self.exchange.create_order(
                        symbol=symbol,
                        side='sell',
                        type=decision.get('order_type', 'market'),
                        amount=decision['amount'],
                        price=decision.get('price')
                    )
                    logger.info(f"Verkaufsorder ausgeführt: {order}")
                else:
                    logger.warning(f"Unbekannte Aktion '{action}' in Entscheidung: {decision}")
                    continue

                self._record_trade(decision, order, market_data)
            except Exception as e:
                logger.error(f"Fehler bei der Orderausführung: {e}", exc_info=True)

    def _check_position_exits(self, symbol: str, current_price: float) -> List[Dict]:
        """
        Prüft, ob für eine offene Position Exit-Bedingungen erfüllt sind.

        Args:
            symbol: Das zu prüfende Handelssymbol.
            current_price: Der aktuelle Marktpreis.

        Returns:
            Eine Liste von Exit-Signalen (Verkaufssignale).
        """
        exit_signals = []
        position = self.portfolio['positions'].get(symbol)

        if not position:
            return exit_signals

        # Finde den ursprünglichen Trade, um SL/TP zu bekommen
        # Dies ist eine Vereinfachung; in der Praxis würde man die Order-ID speichern
        original_trade = None
        for trade in reversed(self.portfolio['trades']):
            if trade['symbol'] == symbol and trade['side'] == 'buy' and trade['status'] == 'open':
                original_trade = trade
                break

        if not original_trade:
            return exit_signals

        stop_loss = original_trade.get('stop_loss')
        take_profit = original_trade.get('take_profit')

        # Stop-Loss-Prüfung
        if stop_loss and current_price <= stop_loss:
            logger.info(f"🚨 STOP-LOSS ausgelöst für {symbol} bei {current_price:.2f} (Limit: {stop_loss:.2f})")
            exit_signals.append(self.strategy_manager.create_signal(symbol, 'sell', 1.0, 'stop_loss', f'Stop-Loss bei {stop_loss:.2f} erreicht'))

        # Take-Profit-Prüfung
        elif take_profit and current_price >= take_profit:
            logger.info(f"✅ TAKE-PROFIT ausgelöst für {symbol} bei {current_price:.2f} (Limit: {take_profit:.2f})")
            exit_signals.append(self.strategy_manager.create_signal(symbol, 'sell', 1.0, 'take_profit', f'Take-Profit bei {take_profit:.2f} erreicht'))

        return exit_signals

    def _record_trade(self, decision: Dict, order: Dict, market_data: pd.DataFrame = None):
        """Speichert Trade-Informationen, aktualisiert Portfolio und Logging."""
        symbol = order.get('symbol')
        side = decision['action']
        amount = decision['amount']
        price = order.get('price')
        cost = order.get('cost', amount * price)
        fee_info = order.get('fee', {})
        fee = fee_info.get('cost', cost * 0.001) if isinstance(fee_info, dict) else 0.0

        trade_status = 'open' if side == 'buy' else 'closed'

        trade = {
            'id': order.get('id', str(uuid.uuid4())),
            'symbol': symbol,
            'action': side,
            'side': side,
            'amount': amount,
            'price': price,
            'cost': cost,
            'fee': fee,
            'timestamp': datetime.utcnow().isoformat(),
            'status': trade_status,
            'stop_loss': decision.get('stop_loss'),
            'take_profit': decision.get('take_profit'),
            'strategy': decision.get('strategy', 'unknown'),
            'confidence': decision.get('confidence', 0.0),
            'reason': decision.get('reason', ''),
            'risk_reward_ratio': decision.get('risk_reward_ratio'),
            'pnl': 0
        }

        logger.debug(f"[Trade] Aufzeichnung: {trade}")

        if side == 'buy':
            self._execute_buy(symbol, amount, price, cost, fee, trade)
        elif side == 'sell':
            self._execute_sell(symbol, amount, price, cost, fee, trade)

        self.portfolio['trades'].append(trade)

        try:
            self.db.save_trade(trade)
        except Exception as e:
            logger.error(f"Fehler beim Speichern des Trades in DB: {e}")

        if self.continuous_learning_enabled and market_data is not None:
            self._track_trade_for_learning(trade, market_data)

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
        
        # Speichere Position in DB
        try:
            self.db.save_position({
                'symbol': symbol,
                'amount': self.portfolio['positions'][symbol]['amount'],
                'entry_price': self.portfolio['positions'][symbol]['avg_price'],
                'current_price': price,
                'pnl': 0.0,
                'pnl_percent': 0.0,
                'opened_at': self.portfolio['positions'][symbol]['entry_time']
            })
        except Exception as e:
            logger.error(f"Fehler beim Speichern der Position in DB: {e}")
        
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
            # Lösche Position aus DB
            try:
                self.db.delete_position(symbol)
            except Exception as e:
                logger.error(f"Fehler beim Löschen der Position aus DB: {e}")
            logger.info(f"Position {symbol} geschlossen")
        else:
            # Aktualisiere Position in DB
            try:
                self.db.save_position({
                    'symbol': symbol,
                    'amount': pos['amount'],
                    'entry_price': pos['avg_price'],
                    'current_price': price,
                    'pnl': pnl,
                    'pnl_percent': (pnl / pos['total_cost']) * 100 if pos['total_cost'] > 0 else 0.0,
                    'opened_at': pos['entry_time']
                })
            except Exception as e:
                logger.error(f"Fehler beim Aktualisieren der Position in DB: {e}")
        
        new_balance = self.portfolio['balance']
        logger.info(f"Verkauf ausgeführt: +{proceeds:.2f} EUR, P&L: {pnl:+.2f} EUR, Neue Balance: {new_balance:.2f} EUR")
        
        # Für Continuous Learning: Outcome sammeln
        if self.continuous_learning_enabled:
            self._collect_trade_outcome(trade, pnl, price)
    
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
        """Speichert den aktuellen Portfolio-Status in die SQLite Datenbank."""
        try:
            self.db.save_portfolio(self.portfolio)
            logger.debug("Portfolio-Status in Datenbank gespeichert")
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
    
    def _track_trade_for_learning(self, trade: Dict, market_data: pd.DataFrame):
        """
        Tracked einen Trade für späteres Continuous Learning.
        
        Args:
            trade: Trade-Informationen
            market_data: Marktdaten zum Zeitpunkt des Trades
        """
        try:
            if trade['side'] != 'buy':
                return  # Nur Buy-Trades tracken
            
            # Extrahiere Features
            features = self.ml_model._prepare_features(market_data)
            
            if features is not None:
                self.open_trades_tracking[trade['id']] = {
                    'trade': trade,
                    'features': features,
                    'entry_time': datetime.utcnow()
                }
                logger.debug(f"Trade {trade['id']} für Learning getrackt")
        
        except Exception as e:
            logger.error(f"Fehler beim Tracking des Trades: {e}")
    
    def _collect_trade_outcome(self, trade: Dict, pnl: float, exit_price: float):
        """
        Sammelt das Outcome eines geschlossenen Trades.
        
        Args:
            trade: Trade-Informationen
            pnl: Profit/Loss
            exit_price: Ausstiegspreis
        """
        try:
            # Finde den entsprechenden Entry-Trade
            entry_trade_id = None
            for tid, tracked in self.open_trades_tracking.items():
                if tracked['trade']['symbol'] == trade['symbol']:
                    entry_trade_id = tid
                    break
            
            if entry_trade_id is None:
                logger.debug(f"Kein Entry-Trade gefunden für Outcome-Collection")
                return
            
            tracked_data = self.open_trades_tracking[entry_trade_id]
            entry_price = tracked_data['trade']['price']
            
            # Berechne P&L Prozent
            pnl_percent = (pnl / (entry_price * tracked_data['trade']['amount'])) * 100
            
            # Erstelle Outcome
            outcome = {
                'pnl': pnl,
                'pnl_percent': pnl_percent,
                'exit_price': exit_price,
                'exit_time': datetime.utcnow().isoformat(),
                'holding_period': (datetime.utcnow() - tracked_data['entry_time']).total_seconds() / 3600
            }
            
            # Sammle Daten
            self.data_collector.collect_trade_outcome(
                trade=tracked_data['trade'],
                features=tracked_data['features'],
                outcome=outcome
            )
            
            # Entferne aus Tracking
            del self.open_trades_tracking[entry_trade_id]
            
            logger.info(f"Trade-Outcome gesammelt: P&L={pnl_percent:+.2f}%")
        
        except Exception as e:
            logger.error(f"Fehler beim Sammeln des Trade-Outcomes: {e}")
    
    def _check_and_retrain(self):
        """Prüft ob Retraining notwendig ist und führt es aus."""
        try:
            if not hasattr(self, 'continuous_learner'):
                return
            
            if self.continuous_learner.should_retrain():
                logger.info("🔄 Starte automatisches Retraining...")
                success = self.continuous_learner.retrain_model()
                
                if success:
                    # Zeige Verbesserungsstatistiken
                    stats = self.continuous_learner.get_improvement_stats()
                    if stats['improvement'] is not None:
                        logger.info(f"✓ Modell-Verbesserung: {stats['improvement']:+.2%} (von {stats['first_accuracy']:.2%} auf {stats['current_accuracy']:.2%})")
                    else:
                        logger.info(f"✓ Erstes Training abgeschlossen")
        
        except Exception as e:
            logger.error(f"Fehler beim Auto-Retraining: {e}")
    
    def get_learning_stats(self) -> Dict:
        """
        Gibt Statistiken über das kontinuierliche Lernen zurück.
        
        Returns:
            Dictionary mit Learning-Statistiken
        """
        if not self.continuous_learning_enabled:
            return {'enabled': False}
        
        data_stats = self.data_collector.get_statistics()
        improvement_stats = self.continuous_learner.get_improvement_stats()
        
        return {
            'enabled': True,
            'collected_samples': data_stats['total_samples'],
            'successful_trades': data_stats['successful_trades'],
            'failed_trades': data_stats['failed_trades'],
            'total_retrains': improvement_stats['total_retrains'],
            'model_improvement': improvement_stats.get('improvement_percent', 0),
            'current_accuracy': improvement_stats.get('current_accuracy', 0)
        }


def main():
    """Hauptfunktion zum Starten des Trading-Bots."""
    # Konfiguration anpassen (optional)
    # 🧠 KI-gesteuerte Konfiguration: Priorisiert die Vorhersagen des trainierten Modells.
    config = {
        'settings': {
            'initial_balance': 1000.0,  # 1000€ Startkapital für sinnvolle Positions-Größen
            'risk_per_trade': 1.0,  # 1% Risiko pro Trade, da KI-Signale präziser sind
            'use_enhanced_pipeline': False,  # Legacy Pipeline nutzen, um die reine ML-Strategie zu verwenden
            'continuous_learning': True,  # Aktiviere kontinuierliches Lernen
            'min_samples_retrain': 50,  # Schnelleres Nachtrainieren mit neuen Live-Daten
            'retrain_frequency_hours': 24,  # Retraining alle 24 Stunden
        },
        'strategies': {
            # Deaktiviere einfache Strategien, um die KI entscheiden zu lassen
            'trend_following': {'enabled': False},
            'mean_reversion': {'enabled': False},
            'breakout': {'enabled': False},
            # Aktiviere NUR die KI-basierte Strategie mit einer soliden Konfidenzschwelle
            'ml_based': {'enabled': True, 'min_confidence': 0.70},
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
