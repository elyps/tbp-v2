"""
Historical Data Trainer - Trainiert das Modell mit historischen Chart-Daten.
Kann Jahre von Daten verarbeiten und Labels automatisch generieren.
"""

import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import os
from tqdm import tqdm

logger = logging.getLogger(__name__)


class HistoricalTrainer:
    """
    Trainiert ML-Modelle mit historischen Marktdaten (bis zu 15 Jahre).
    """
    
    def __init__(self, data_provider, indicators, ml_model, news_provider=None):
        """
        Initialisiert den Historical Trainer.
        
        Args:
            data_provider: DataProvider Instanz
            indicators: TechnicalIndicators Instanz
            ml_model: MLModel Instanz
            news_provider: Optional NewsProvider für News-Features
        """
        self.data_provider = data_provider
        self.indicators = indicators
        self.ml_model = ml_model
        self.news_provider = news_provider
        
        logger.info("HistoricalTrainer initialisiert")
    
    def train_on_historical_data(
        self,
        symbols: List[str],
        years: int = 15,
        timeframe: str = '1d',
        forward_window: int = 10,
        profit_threshold: float = 0.01,
        use_news: bool = False
    ) -> Dict:
        """
        Trainiert das Modell mit historischen Daten mehrerer Jahre.
        
        Args:
            symbols: Liste von Symbolen (z.B. ['BTC/USDT', 'ETH/USDT'])
            years: Anzahl Jahre historische Daten (Standard: 15)
            timeframe: Zeitrahmen ('1h', '4h', '1d', '1w')
            forward_window: Blick in die Zukunft für Labels (Kerzen)
            profit_threshold: Mindestgewinn für positives Label (0.01 = 1%)
            use_news: Ob News-Sentiment-Features verwendet werden sollen
            
        Returns:
            Dict mit Trainings-Statistiken
        """
        logger.info(f"Starte Historical Training: {len(symbols)} Symbole, {years} Jahre, Timeframe: {timeframe}")
        
        all_features = []
        all_labels = []
        stats = {
            'symbols_processed': 0,
            'total_samples': 0,
            'positive_samples': 0,
            'negative_samples': 0,
            'neutral_samples': 0,
            'errors': []
        }
        
        # Verarbeite jedes Symbol
        for symbol in tqdm(symbols, desc="Verarbeite Symbole"):
            try:
                logger.info(f"Lade historische Daten für {symbol}...")
                
                # Berechne Anzahl der Kerzen basierend auf Jahren und Timeframe
                limit = self._calculate_limit(years, timeframe)
                
                # Lade historische Daten
                df = self.data_provider.get_historical_data(
                    symbol=symbol,
                    timeframe=timeframe,
                    limit=limit
                )
                
                if df is None or df.empty or len(df) < 100:
                    logger.warning(f"Nicht genug Daten für {symbol} - überspringe")
                    stats['errors'].append(f"{symbol}: Nicht genug Daten")
                    continue
                
                # Liquiditäts-Check: Überspringe illiquide Märkte
                # Mindestens 1 Mio. USD/EUR/etc. durchschnittliches Tagesvolumen
                avg_daily_volume_quote = (df['close'] * df['volume']).mean()
                min_liquidity_threshold = 1_000_000
                if avg_daily_volume_quote < min_liquidity_threshold:
                    logger.warning(f"{symbol}: Geringe Liquidität ({avg_daily_volume_quote:,.0f} < {min_liquidity_threshold:,.0f}) - überspringe")
                    stats['errors'].append(f"{symbol}: Geringe Liquidität")
                    continue

                logger.info(f"{symbol}: {len(df)} Kerzen geladen (von {df.index[0]} bis {df.index[-1]})")
                
                # Berechne technische Indikatoren
                df_indicators = self.indicators.calculate_all(df)
                
                # Füge News-Features hinzu (falls aktiviert)
                if use_news and self.news_provider:
                    df_indicators = self._add_news_features(df_indicators, symbol)
                
                # Generiere Labels basierend auf zukünftigen Preisen
                labels = self._generate_labels(
                    df_indicators,
                    forward_window=forward_window,
                    profit_threshold=profit_threshold
                )
                
                # Extrahiere Features für jede Kerze
                features = self._extract_features_batch(df_indicators)
                
                # Kombiniere mit Labels
                valid_samples = min(len(features), len(labels))
                features = features[:valid_samples]
                labels = labels[:valid_samples]
                
                all_features.append(features)
                all_labels.extend(labels)
                
                # Statistiken aktualisieren
                stats['symbols_processed'] += 1
                stats['total_samples'] += len(labels)
                stats['positive_samples'] += sum(1 for l in labels if l == 2)
                stats['negative_samples'] += sum(1 for l in labels if l == 0)
                stats['neutral_samples'] += sum(1 for l in labels if l == 1)
                
                logger.info(f"{symbol}: {len(labels)} Samples generiert")
            
            except Exception as e:
                logger.error(f"Fehler beim Verarbeiten von {symbol}: {e}", exc_info=True)
                stats['errors'].append(f"{symbol}: {str(e)}")
        
        # Kombiniere alle Features
        if all_features:
            X = pd.concat(all_features, ignore_index=True)
            y = pd.Series(all_labels)
            
            logger.info(f"Gesamtdaten: {len(X)} Samples aus {stats['symbols_processed']} Symbolen")
            logger.info(f"Label-Verteilung: Kauf={stats['positive_samples']}, Halten={stats['neutral_samples']}, Verkauf={stats['negative_samples']}")
            
            # Trainiere Modell
            logger.info("Starte Modell-Training mit historischen Daten...")
            self.ml_model.train(X, y)
            
            # Evaluiere
            accuracy = self.ml_model.model.score(self.ml_model.scaler.transform(X), y)
            stats['training_accuracy'] = accuracy
            
            logger.info(f"✓ Historical Training abgeschlossen - Accuracy: {accuracy:.2%}")
        else:
            logger.error("Keine Daten für Training gesammelt!")
            stats['training_accuracy'] = 0.0
        
        return stats
    
    def _calculate_limit(self, years: int, timeframe: str) -> int:
        """Berechnet die Anzahl der Kerzen basierend auf Jahren und Timeframe."""
        # Kerzen pro Jahr (ungefähr)
        candles_per_year = {
            '1m': 525600,     # 1 Min
            '5m': 105120,     # 5 Min
            '15m': 35040,     # 15 Min
            '1h': 8760,       # 1 Stunde
            '4h': 2190,       # 4 Stunden
            '1d': 365,        # 1 Tag
            '1w': 52,         # 1 Woche
            '1M': 12          # 1 Monat
        }
        
        candles_per_year_value = candles_per_year.get(timeframe, 8760)  # Default: 1h
        return min(years * candles_per_year_value, 10000)  # Max 10000 Kerzen pro API-Call
    
    def _generate_labels(
        self,
        df: pd.DataFrame,
        forward_window: int = 10,
        profit_threshold: float = 0.01
    ) -> List[int]:
        """
        Generiert Labels basierend auf zukünftigen Preis-Bewegungen.
        
        Args:
            df: DataFrame mit OHLCV-Daten
            forward_window: Anzahl Kerzen in die Zukunft schauen
            profit_threshold: Mindestgewinn für positives Label
            
        Returns:
            Liste von Labels (0=Verkauf, 1=Halten, 2=Kauf)
        """
        logger.info(f"Generiere risikobewusste Labels (Window: {forward_window}, R/R: 1.5)...")
        labels = []
        close_prices = df['close'].values
        high_prices = df['high'].values
        low_prices = df['low'].values
        atr_values = df['atr'].values if 'atr' in df.columns else [p * 0.02 for p in close_prices]
        
        risk_reward_ratio = 1.5
        
        for i in range(len(df) - forward_window):
            current_price = close_prices[i]
            atr = atr_values[i]
            
            # Definiere Stop-Loss und Take-Profit für diesen Punkt
            stop_loss_price = current_price - (atr * 2.0)
            take_profit_price = current_price + (atr * 2.0 * risk_reward_ratio)
            
            # Prüfe die zukünftigen Kerzen
            future_lows = low_prices[i+1 : i+1+forward_window]
            future_highs = high_prices[i+1 : i+1+forward_window]
            
            sl_hit = False
            tp_hit = False
            
            # Finde heraus, was zuerst getroffen wird
            for j in range(len(future_lows)):
                if future_lows[j] <= stop_loss_price:
                    sl_hit = True
                    break # Stop-Loss wurde getroffen
                if future_highs[j] >= take_profit_price:
                    tp_hit = True
                    break # Take-Profit wurde getroffen
            
            if tp_hit and not sl_hit:
                # Take-Profit wurde erreicht, bevor Stop-Loss -> Guter Kauf
                labels.append(2)
            elif sl_hit and not tp_hit:
                # Stop-Loss wurde erreicht, bevor Take-Profit -> Schlechter Kauf
                labels.append(0)
            else:
                # Keines von beiden wurde im Fenster erreicht -> Halten
                labels.append(1)
        
        # Fülle die restlichen Labels auf, für die wir keine Zukunft haben
        while len(labels) < len(df):
            labels.append(1) # Neutral
        
        return labels
    
    def _extract_features_batch(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Extrahiert Features für alle Zeilen im DataFrame.
        
        Args:
            df: DataFrame mit Indikatoren
            
        Returns:
            DataFrame mit Features
        """
        features_list = []
        
        for idx in range(len(df)):
            # Nutze die _prepare_features Methode des ML-Modells
            # Erstelle temporären DataFrame mit nur dieser Zeile
            row_df = df.iloc[:idx+1].copy()  # Inkludiere Historie bis zu diesem Punkt
            
            if len(row_df) >= 50:  # Mindestens 50 Kerzen für gültige Indikatoren
                features = self.ml_model._prepare_features(row_df)
                if features is not None and not features.empty:
                    features_list.append(features)
        
        if features_list:
            return pd.concat(features_list, ignore_index=True)
        return pd.DataFrame()
    
    def _add_news_features(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """
        Fügt News-Sentiment-Features zu historischen Daten hinzu.
        
        Args:
            df: DataFrame mit Marktdaten
            symbol: Trading-Symbol
            
        Returns:
            DataFrame mit zusätzlichen News-Features
        """
        try:
            # Hole aktuelles News-Sentiment
            news_features = self.news_provider.get_news_features(symbol)
            
            # Füge als konstante Spalten hinzu (da historische News schwer zu bekommen sind)
            for feature_name, value in news_features.items():
                df[feature_name] = value
            
            logger.debug(f"News-Features für {symbol} hinzugefügt")
        
        except Exception as e:
            logger.warning(f"Fehler beim Hinzufügen von News-Features: {e}")
            # Füge Default-Werte hinzu
            df['news_sentiment_score'] = 0.0
            df['news_sentiment_positive'] = 0
            df['news_sentiment_negative'] = 0
            df['news_volume'] = 0
            df['news_positive_ratio'] = 0.0
            df['news_negative_ratio'] = 0.0
            df['news_confidence'] = 0.0
        
        return df
    
    def backtest_on_historical_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        timeframe: str = '1d',
        initial_balance: float = 10000.0
    ) -> Dict:
        """
        Backtesting mit historischen Daten und trainiertem Modell.
        
        Args:
            symbol: Trading-Symbol
            start_date: Start-Datum (YYYY-MM-DD)
            end_date: End-Datum (YYYY-MM-DD)
            timeframe: Zeitrahmen
            initial_balance: Startkapital
            
        Returns:
            Dict mit Backtest-Ergebnissen
        """
        logger.info(f"Starte Backtest für {symbol} von {start_date} bis {end_date}")
        
        # Lade Daten
        df = self.data_provider.get_historical_data(
            symbol=symbol,
            timeframe=timeframe,
            limit=5000
        )
        
        if df is None or df.empty:
            logger.error("Keine Daten für Backtest verfügbar")
            return {}
        
        # Filter nach Datum
        df = df[(df.index >= start_date) & (df.index <= end_date)]
        
        # Indikatoren berechnen
        df_indicators = self.indicators.calculate_all(df)
        
        # Simulation
        balance = initial_balance
        position = 0
        position_entry_price = 0
        trades = []
        stop_loss_price = 0.0
        take_profit_price = 0.0
        risk_reward_ratio = 1.2  # Aggressiver für Day-Trading: 1.2
        
        for i in range(len(df_indicators)):
            row_df = df_indicators.iloc[:i+1]
            
            if len(row_df) < 50:
                continue
            
            # Vorhersage
            prediction = self.ml_model.predict(row_df)
            signal = prediction['signal']
            confidence = prediction['confidence']
            
            current_price = df_indicators['close'].iloc[i]
            
            # --- Exit-Logik (Stop-Loss / Take-Profit) ---
            if position > 0:
                # Stop-Loss prüfen
                if current_price <= stop_loss_price:
                    reason = 'STOP-LOSS'
                    sell_value = position * stop_loss_price  # Ausführung zum SL-Preis
                    pnl = sell_value - (position * position_entry_price)
                    balance += sell_value
                    trades.append({'type': 'SELL', 'price': stop_loss_price, 'amount': position, 'pnl': pnl, 'pnl_percent': (pnl / (position * position_entry_price)) * 100, 'date': df_indicators.index[i], 'reason': reason})
                    position = 0
                    logger.info(f"  -> {reason} bei ${stop_loss_price:.2f}, P&L: ${pnl:.2f}")
                    continue
                
                # Take-Profit prüfen
                if current_price >= take_profit_price:
                    reason = 'TAKE-PROFIT'
                    sell_value = position * take_profit_price # Ausführung zum TP-Preis
                    pnl = sell_value - (position * position_entry_price)
                    balance += sell_value
                    trades.append({'type': 'SELL', 'price': take_profit_price, 'amount': position, 'pnl': pnl, 'pnl_percent': (pnl / (position * position_entry_price)) * 100, 'date': df_indicators.index[i], 'reason': reason})
                    position = 0
                    logger.info(f"  -> {reason} bei ${take_profit_price:.2f}, P&L: ${pnl:.2f}")
                    continue

            # --- Entry-Logik (Kaufen) ---
            if signal == 1 and position == 0 and confidence > 0.65:  # Konfidenz für mehr Trades leicht gesenkt
                # Kaufe Position
                amount = balance * 0.95 / current_price  # 95% des Kapitals
                position = amount
                position_entry_price = current_price
                balance -= amount * current_price
                
                # Setze Stop-Loss und Take-Profit
                atr = df_indicators['atr'].iloc[i] if 'atr' in df_indicators.columns else current_price * 0.02
                stop_loss_price = current_price - (atr * 1.5) # Engerer Stop-Loss für kurzfristige Trades
                profit_target = current_price + (atr * 2.0 * risk_reward_ratio)
                take_profit_price = profit_target
                
                trades.append({'type': 'BUY', 'price': current_price, 'amount': amount, 'date': df_indicators.index[i]})
                logger.info(f"  -> KAUF bei ${current_price:.2f}, SL: ${stop_loss_price:.2f}, TP: ${take_profit_price:.2f}")
            
            # --- Exit-Logik (Verkaufen basierend auf Signal) ---
            elif signal == -1 and position > 0 and confidence > 0.6:  # Verkaufen
                # Verkaufe Position
                sell_value = position * current_price
                pnl = sell_value - (position * position_entry_price)
                balance += sell_value
                trades.append({'type': 'SELL', 'price': current_price, 'amount': position, 'pnl': pnl, 'pnl_percent': (pnl / (position * position_entry_price)) * 100, 'date': df_indicators.index[i], 'reason': 'Signal'})
                logger.info(f"  -> VERKAUF (Signal) bei ${current_price:.2f}, P&L: ${pnl:.2f}")
                position = 0
        
        # Schließe offene Position
        if position > 0:
            final_value = position * df_indicators['close'].iloc[-1]
            pnl = final_value - (position * position_entry_price)
            balance += final_value
            
            trades.append({'type': 'SELL (Final)', 'price': df_indicators['close'].iloc[-1], 'amount': position, 'pnl': pnl, 'pnl_percent': (pnl / (position * position_entry_price)) * 100, 'date': df_indicators.index[-1], 'reason': 'End of Backtest'})
        
        # Statistiken
        final_balance = balance
        total_return = ((final_balance - initial_balance) / initial_balance) * 100
        
        winning_trades = [t for t in trades if t.get('pnl', 0) > 0]
        losing_trades = [t for t in trades if t.get('pnl', 0) < 0]
        
        results = {
            'initial_balance': initial_balance,
            'final_balance': final_balance,
            'total_return': total_return,
            'total_trades': len([t for t in trades if 'pnl' in t]),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': len(winning_trades) / max(len(winning_trades) + len(losing_trades), 1) * 100,
            'avg_profit': sum(t['pnl'] for t in winning_trades) / max(len(winning_trades), 1) if winning_trades else 0,
            'avg_loss': sum(t['pnl'] for t in losing_trades) / max(len(losing_trades), 1) if losing_trades else 0,
            'trades': trades
        }
        
        logger.info(f"Backtest abgeschlossen: Return={total_return:.2f}%, Win-Rate={results['win_rate']:.1f}%")
        return results
