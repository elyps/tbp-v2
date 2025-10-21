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
        years: int = 3,  # Für 15m sind 3 Jahre mehr als genug Daten
        timeframe: str = '15m', # Wechsel auf kürzeren Timeframe für mehr Trades
        forward_window: int = 12,     # 3 Stunden auf einem 15m Chart
        profit_threshold: float = 0.005,  # Gesenkt für mehr Gelegenheiten (0.5%)
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

                # Füge On-Chain-Features hinzu (als Platzhalter für historisches Training)
                df_indicators = self._add_onchain_features(df_indicators)
                
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
    
    def _calculate_limit(self, years: float, timeframe: str) -> int:
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
        return int(years * candles_per_year_value)
    
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
        logger.info(f"Generiere Scalping-Labels (Window: {forward_window}, Profit-Schwelle: {profit_threshold * 100:.2f}%)...")
        labels = []
        close_prices = df['close'].values
        high_prices = df['high'].values
        low_prices = df['low'].values
        
        for i in range(len(df) - forward_window):
            current_price = close_prices[i]
            if current_price == 0: # Preis von 0 vermeiden
                labels.append(1) # Neutral
                continue

            # Definiere dynamische Schwellen basierend auf dem aktuellen Preis
            profit_target_price = current_price * (1 + profit_threshold)
            loss_stop_price = current_price * (1 - profit_threshold)
            
            # Prüfe die zukünftigen Kerzen
            future_lows = low_prices[i+1 : i+1+forward_window]
            future_highs = high_prices[i+1 : i+1+forward_window]
            
            tp_hit_idx = -1
            sl_hit_idx = -1
            
            # Finde heraus, was zuerst getroffen wird
            for j in range(len(future_lows)):
                if future_highs[j] >= profit_target_price:
                    tp_hit_idx = j
                    break
                if future_lows[j] <= loss_stop_price:
                    sl_hit_idx = j
                    break
            
            if tp_hit_idx != -1 and (sl_hit_idx == -1 or tp_hit_idx < sl_hit_idx):
                # Take-Profit wurde zuerst erreicht -> Guter Kauf
                label = 2  # KAUFEN
            elif sl_hit_idx != -1 and (tp_hit_idx == -1 or sl_hit_idx < tp_hit_idx):
                # Stop-Loss wurde zuerst erreicht -> Schlechter Kauf / Verkauf
                label = 0  # VERKAUFEN
            else:
                # Weder TP noch SL wurden im Fenster erreicht -> Halten
                label = 1  # HALTEN
            
            labels.append(label)
        
        # Fülle die restlichen Labels auf, für die wir keine Zukunft haben
        while len(labels) < len(df):
            labels.append(1) # Neutral
        
        return labels
    
    def _extract_features_batch(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Extrahiert Features für alle Zeilen im DataFrame auf eine vektorisierte,
        schnelle Weise.
        
        Args:
            df: DataFrame mit Indikatoren
            
        Returns:
            DataFrame mit Features, bereit für das Training.
        """
        # 1. Erstelle alle abgeleiteten Features in einem Rutsch (vektorisiert)
        all_features_df = self.ml_model._create_features_from_indicators(df)
        
        # 2. Wähle die finalen Feature-Spalten aus, die das Modell erwartet
        features_df = self.ml_model._select_features_from_df(all_features_df)
        
        # Entferne Zeilen mit NaN-Werten, die durch Indikatoren-Berechnungen entstehen
        # Dies entfernt die ersten N Zeilen, für die Indikatoren wie SMA50 noch nicht berechnet werden können
        features_df.dropna(inplace=True)
        
        return features_df
    
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

    def _add_onchain_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Fügt Platzhalter für On-Chain- und Futures-Daten hinzu.
        Im Live-Betrieb würden hier echte Daten von einem Provider geladen.
        """
        onchain_features = {
            # Netzwerk-Aktivität
            'active_addresses': 0.0,
            'transaction_count': 0.0,
            'transaction_volume': 0.0,
            # Börsen-Flows
            'exchange_inflow': 0.0,
            'exchange_outflow': 0.0,
            'exchange_netflow': 0.0,
            # Wal-Aktivität
            'whale_inflow': 0.0,
            'whale_outflow': 0.0,
            # Futures-Markt
            'futures_open_interest': 0.0,
            'futures_funding_rate': 0.0,
            'futures_long_liquidations': 0.0,
            'futures_short_liquidations': 0.0,
            # Bewertungsmetriken
            'nvt_signal': 0.0, 'sopr': 1.0, 'mvrv_z_score': 0.0
        }
        for feature, value in onchain_features.items():
            df[feature] = value
        logger.debug("Platzhalter für On-Chain-Features hinzugefügt.")
        return df
    
    def backtest_on_historical_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        timeframe: str = '15m', # Backtest auf dem gleichen Timeframe wie das Training
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
        
        # Berechne die Anzahl der benötigten Kerzen für den Zeitraum
        start_dt = datetime.fromisoformat(start_date)
        end_dt = datetime.fromisoformat(end_date)
        days = (end_dt - start_dt).days + 1 # +1 um den Endtag einzuschließen
        limit = self._calculate_limit(days / 365, timeframe)
        
        # Lade Daten
        df = self.data_provider.get_historical_data(
            symbol=symbol, timeframe=timeframe, limit=limit
        )
        
        if df is None or df.empty:
            logger.error("Keine Daten für Backtest verfügbar")
            return {}
        
        # Filter nach Datum
        df = df[(df.index >= start_date) & (df.index <= end_date)]
        
        # Indikatoren berechnen
        df_indicators = self.indicators.calculate_all(df)
        
        # On-Chain Features hinzufügen (Platzhalter)
        df_indicators = self._add_onchain_features(df_indicators)
        
        # Simulation
        balance = initial_balance
        position = 0  # 0: flat, >0: long, <0: short
        position_entry_price = 0
        trades = []
        stop_loss_price = 0.0
        highest_price_since_entry = 0.0  # For long trades
        lowest_price_since_entry = float('inf') # For short trades
        
        for i in tqdm(range(len(df_indicators)), desc="Backtesting"):
            row_df = df_indicators.iloc[:i+1]
            
            if len(row_df) < 50:
                continue
            
            # Vorhersage
            prediction = self.ml_model.predict(row_df)
            signal = prediction['signal']
            confidence = prediction['confidence']
            
            current_price = df_indicators['close'].iloc[i]
            
            # --- Exit-Logik für LONG Position ---
            if position > 0:
                # Update höchsten Preis für Trailing Stop
                highest_price_since_entry = max(highest_price_since_entry, current_price)
                
                # Trailing Stop-Loss Logik: Passe den Stop-Loss nach oben an
                atr_val = df_indicators['atr'].iloc[i] if 'atr' in df_indicators.columns else current_price * 0.02
                new_stop_loss = highest_price_since_entry - (atr_val * 1.8) # Engerer Trailing Stop für schnellere Exits
                stop_loss_price = max(stop_loss_price, new_stop_loss)

                # Stop-Loss prüfen
                if current_price <= stop_loss_price:
                    reason = 'LONG TRAILING STOP' if stop_loss_price > (position_entry_price - (atr_val * 1.5)) else 'LONG STOP-LOSS'
                    sell_value = position * stop_loss_price  # Ausführung zum SL-Preis
                    pnl = sell_value - (position * position_entry_price)
                    balance += sell_value
                    trades.append({'type': 'SELL', 'price': stop_loss_price, 'amount': position, 'pnl': pnl, 'pnl_percent': (pnl / (position * position_entry_price)) * 100, 'date': df_indicators.index[i], 'reason': reason})
                    position = 0
                    logger.info(f"  -> {reason} bei ${stop_loss_price:.2f}, P&L: ${pnl:.2f}")
                    continue
            
            # --- Exit-Logik für SHORT Position ---
            elif position < 0:
                # Update niedrigsten Preis für Trailing Stop
                lowest_price_since_entry = min(lowest_price_since_entry, current_price)
                
                # Trailing Stop-Loss Logik: Passe den Stop-Loss nach unten an
                atr_val = df_indicators['atr'].iloc[i] if 'atr' in df_indicators.columns else current_price * 0.02
                new_stop_loss = lowest_price_since_entry + (atr_val * 1.8) # Engerer Trailing Stop
                stop_loss_price = min(stop_loss_price, new_stop_loss)
                
                # Stop-Loss prüfen (Preis steigt über SL)
                if current_price >= stop_loss_price:
                    reason = 'SHORT TRAILING STOP' if stop_loss_price < (position_entry_price + (atr_val * 1.5)) else 'SHORT STOP-LOSS'
                    buy_back_value = abs(position) * stop_loss_price
                    pnl = (abs(position) * position_entry_price) - buy_back_value
                    balance -= (buy_back_value - (abs(position) * position_entry_price))
                    trades.append({'type': 'COVER', 'price': stop_loss_price, 'amount': abs(position), 'pnl': pnl, 'pnl_percent': (pnl / (abs(position) * position_entry_price)) * 100, 'date': df_indicators.index[i], 'reason': reason})
                    position = 0
                    logger.info(f"  -> {reason} bei ${stop_loss_price:.2f}, P&L: ${pnl:.2f}")
                    continue

            # --- Entry-Logik (Kaufen) ---
            if signal == 1 and position == 0 and confidence > 0.50:  # Maximale Aggressivität für höchste Trade-Frequenz
                # Kaufe Position
                amount = (balance * 0.75) / current_price  # Erhöhter Kapitaleinsatz (75%)
                position = amount
                position_entry_price = current_price
                balance -= amount * current_price
                
                # Setze initialen Stop-Loss basierend auf ATR
                atr_val = df_indicators['atr'].iloc[i] if 'atr' in df_indicators.columns else current_price * 0.02
                stop_loss_price = current_price - (atr_val * 1.5) # Initialer Stop-Loss
                highest_price_since_entry = current_price # Reset für neuen Trade
                trades.append({'type': 'BUY', 'price': current_price, 'amount': amount, 'date': df_indicators.index[i]})
                logger.info(f"  -> KAUF bei ${current_price:.2f}, Initial-SL: ${stop_loss_price:.2f}")
            
            # --- Entry-Logik (Shorten) ---
            elif signal == -1 and position == 0 and confidence > 0.50: # Maximale Aggressivität für höchste Trade-Frequenz
                # Verkaufe (short) Position
                amount = (balance * 0.75) / current_price
                position = -amount # Negative Position für Short
                position_entry_price = current_price
                # Balance ändert sich beim Shorten nicht direkt, erst beim Schließen
                
                # Setze initialen Stop-Loss (über dem Preis)
                atr_val = df_indicators['atr'].iloc[i] if 'atr' in df_indicators.columns else current_price * 0.02
                stop_loss_price = current_price + (atr_val * 1.5)
                lowest_price_since_entry = current_price # Reset für neuen Trade
                trades.append({'type': 'SHORT', 'price': current_price, 'amount': amount, 'date': df_indicators.index[i]})
                logger.info(f"  -> SHORT bei ${current_price:.2f}, Initial-SL: ${stop_loss_price:.2f}")

            # --- Exit-Logik (Gegensignal) ---
            elif signal == -1 and position > 0 and confidence > 0.6:  # Verkaufssignal schließt Long-Position
                # Verkaufe Position
                sell_value = position * current_price
                pnl = sell_value - (position * position_entry_price)
                balance += sell_value
                trades.append({'type': 'SELL', 'price': current_price, 'amount': position, 'pnl': pnl, 'pnl_percent': (pnl / (position * position_entry_price)) * 100, 'date': df_indicators.index[i], 'reason': 'Signal'})
                logger.info(f"  -> VERKAUF (Signal) bei ${current_price:.2f}, P&L: ${pnl:.2f}")
                position = 0
            
            elif signal == 1 and position < 0 and confidence > 0.6: # Kaufsignal schließt Short-Position
                # Kaufe Position zurück (cover)
                buy_back_value = abs(position) * current_price
                pnl = (abs(position) * position_entry_price) - buy_back_value
                balance -= (buy_back_value - (abs(position) * position_entry_price))
                trades.append({'type': 'COVER', 'price': current_price, 'amount': abs(position), 'pnl': pnl, 'pnl_percent': (pnl / (abs(position) * position_entry_price)) * 100, 'date': df_indicators.index[i], 'reason': 'Signal'})
                logger.info(f"  -> COVER (Signal) bei ${current_price:.2f}, P&L: ${pnl:.2f}")
                position = 0
        
        # Schließe offene Position
        if position > 0:
            final_value = position * df_indicators['close'].iloc[-1]
            pnl = final_value - (position * position_entry_price)
            balance += final_value
            trades.append({'type': 'SELL (Final)', 'price': df_indicators['close'].iloc[-1], 'amount': position, 'pnl': pnl, 'pnl_percent': (pnl / (position * position_entry_price)) * 100, 'date': df_indicators.index[-1], 'reason': 'End of Backtest'})
        elif position < 0:
            buy_back_value = abs(position) * df_indicators['close'].iloc[-1]
            pnl = (abs(position) * position_entry_price) - buy_back_value
            balance -= (buy_back_value - (abs(position) * position_entry_price))
            trades.append({'type': 'COVER (Final)', 'price': df_indicators['close'].iloc[-1], 'amount': abs(position), 'pnl': pnl, 'pnl_percent': (pnl / (abs(position) * position_entry_price)) * 100, 'date': df_indicators.index[-1], 'reason': 'End of Backtest'})
        
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
