"""
Strategie-Manager für verschiedene Handelsstrategien.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class StrategyManager:
    """
    Verwaltet und führt verschiedene Handelsstrategien aus.
    """
    
    def __init__(self, strategies_config: Dict, indicators, ml_model):
        """
        Initialisiert den Strategy-Manager.
        
        Args:
            strategies_config: Konfiguration der Strategien
            indicators: TechnicalIndicators-Instanz
            ml_model: MLModel-Instanz
        """
        self.config = strategies_config
        self.indicators = indicators
        self.ml_model = ml_model
        self.active_strategies = []
        
        # Aktiviere konfigurierte Strategien
        self._initialize_strategies()
        
        logger.info("StrategyManager erfolgreich initialisiert")
    
    def _initialize_strategies(self):
        """Initialisiert die aktiven Strategien basierend auf der Konfiguration."""
        for strategy_name, strategy_config in self.config.items():
            if strategy_config.get('enabled', False):
                self.active_strategies.append(strategy_name)
                logger.info(f"Strategie aktiviert: {strategy_name}")
    
    def evaluate(self, df: pd.DataFrame, predictions: Dict, symbol: str) -> List[Dict]:
        """
        Evaluiert alle aktiven Strategien und gibt Handelssignale zurück.
        
        Args:
            df: DataFrame mit Marktdaten und Indikatoren
            predictions: ML-Vorhersagen
            symbol: Handelssymbol
            
        Returns:
            Liste von Handelssignalen
        """
        signals = []
        
        for strategy_name in self.active_strategies:
            try:
                if strategy_name == 'trend_following':
                    signal = self._trend_following_strategy(df, predictions)
                elif strategy_name == 'mean_reversion':
                    signal = self._mean_reversion_strategy(df)
                elif strategy_name == 'breakout':
                    signal = self._breakout_strategy(df)
                elif strategy_name == 'ml_based':
                    signal = self._ml_based_strategy(df, predictions)
                else:
                    continue
                
                if signal:
                    signal['strategy'] = strategy_name
                    signal['symbol'] = symbol
                    signals.append(signal)
                    
            except Exception as e:
                logger.error(f"Fehler bei Strategie {strategy_name}: {str(e)}")
        
        return signals
    
    def _trend_following_strategy(self, df: pd.DataFrame, predictions: Dict) -> Optional[Dict]:
        """Optimierte Trend-Following Strategie mit Multi-Indikator-Bestätigung."""
        try:
            if len(df) < 50:
                logger.debug("Trend-Following: Nicht genug Daten")
                return None
            
            current = df.iloc[-1]
            prev = df.iloc[-2]
            recent = df.tail(10)
            logger.debug(
                "Trend-Following: price=%.2f prev_price=%.2f sma20=%.2f sma50=%.2f prev_sma20=%.2f prev_sma50=%.2f rsi=%.2f macd_hist=%.5f vol=%.2f avg_vol=%.2f",
                current['close'], prev['close'], current.get('sma_20', float('nan')),
                current.get('sma_50', float('nan')), prev.get('sma_20', float('nan')),
                prev.get('sma_50', float('nan')), current.get('rsi_14', float('nan')),
                current.get('macd_hist', float('nan')), current.get('volume', float('nan')),
                recent['volume'].mean() if 'volume' in recent.columns else float('nan')
            )
            
            # Prüfe ob alle benötigten Indikatoren vorhanden
            required = ['sma_20', 'sma_50', 'rsi_14', 'macd_hist', 'volume']
            if not all(col in df.columns for col in required):
                logger.debug("Trend-Following: Indikatoren fehlen")
                return None
            
            price = current['close']
            sma_20 = current['sma_20']
            sma_50 = current['sma_50']
            rsi = current['rsi_14']
            macd_hist = current['macd_hist']
            volume = current['volume']
            avg_volume = recent['volume'].mean()
            
            if any(pd.isna(v) for v in [sma_20, sma_50, rsi, macd_hist]):
                logger.debug("Trend-Following: Indikator-Werte sind NaN")
                return None
            
            prev_sma_20 = prev['sma_20']
            prev_sma_50 = prev['sma_50']
            prev_macd_hist = prev['macd_hist']
            
            # KAUFSIGNAL: Bullish Crossover MIT Bestätigung
            if sma_20 > sma_50 and prev_sma_20 <= prev_sma_50:
                # Bestätigungen:
                confirmations = 0
                if rsi > 40 and rsi < 70:  # RSI nicht extrem
                    confirmations += 1
                if macd_hist > 0:  # MACD bullish
                    confirmations += 1
                if volume > avg_volume * 1.1:  # Erhöhtes Volumen
                    confirmations += 1
                
                if confirmations >= 1:  # Mindestens 1 Bestätigung
                    logger.info(f"Trend-Following: Bullisher Crossover bestätigt ({confirmations} Checks)")
                    return {
                        'action': 'buy',
                        'confidence': 0.70 + (confirmations * 0.05),
                        'reason': f'Confirmed bullish crossover ({confirmations} signals)'
                    }
            
            # VERKAUFSSIGNAL: Bearish Crossover MIT Bestätigung
            if sma_20 < sma_50 and prev_sma_20 >= prev_sma_50:
                confirmations = 0
                if rsi < 60 and rsi > 30:  # RSI nicht extrem
                    confirmations += 1
                if macd_hist < 0:  # MACD bearish
                    confirmations += 1
                if volume > avg_volume * 1.1:  # Erhöhtes Volumen
                    confirmations += 1
                
                if confirmations >= 1:
                    logger.info(f"Trend-Following: Bearisher Crossover bestätigt ({confirmations} Checks)")
                    return {
                        'action': 'sell',
                        'confidence': 0.70 + (confirmations * 0.05),
                        'reason': f'Confirmed bearish crossover ({confirmations} signals)'
                    }
            
            logger.debug(f"Trend-Following: Keine bestätigten Signale")
            return None
            
        except Exception as e:
            logger.error(f"Fehler in Trend-Following Strategie: {str(e)}")
            return None
    
    def _mean_reversion_strategy(self, df: pd.DataFrame) -> Optional[Dict]:
        """Optimierte Mean Reversion mit strengeren Bedingungen."""
        try:
            if len(df) < 20:
                logger.debug("Mean Reversion: Nicht genug Daten")
                return None
            
            current = df.iloc[-1]
            prev = df.iloc[-2]
            recent = df.tail(5)
            logger.debug(
                "Mean-Reversion: price=%.2f prev_price=%.2f rsi=%.2f prev_rsi=%.2f bb_lower=%.2f bb_upper=%.2f bb_mid=%.2f vol=%.2f avg_vol=%.2f",
                current['close'], prev['close'], current.get('rsi_14', float('nan')),
                prev.get('rsi_14', float('nan')), current.get('bb_lower', float('nan')),
                current.get('bb_upper', float('nan')), current.get('bb_middle', float('nan')),
                current.get('volume', float('nan')), recent['volume'].mean() if 'volume' in recent.columns else float('nan')
            )
            
            required = ['rsi_14', 'bb_lower', 'bb_upper', 'bb_middle', 'volume']
            if not all(col in df.columns for col in required):
                logger.debug("Mean Reversion: Indikatoren fehlen")
                return None
            
            rsi = current['rsi_14']
            prev_rsi = prev['rsi_14']
            price = current['close']
            bb_lower = current['bb_lower']
            bb_upper = current['bb_upper']
            bb_middle = current['bb_middle']
            volume = current['volume']
            avg_volume = recent['volume'].mean()
            
            if any(pd.isna(v) for v in [rsi, prev_rsi, bb_lower, bb_upper, bb_middle]):
                logger.debug("Mean Reversion: Werte sind NaN")
                return None
            
            # KAUFSIGNAL: Stark überverkauft MIT Umkehr-Anzeichen
            if rsi < 30 and prev_rsi < rsi:  # RSI beginnt zu steigen
                # Zusätzliche Filter:
                if price <= bb_lower * 1.02:  # Nahe unterem BB
                    # Prüfe ob Preis vom Tief zurückkehrt
                    recent_low = recent['low'].min()
                    if price > recent_low * 1.001:  # Leichte Erholung
                        logger.info(f"Mean Reversion: Starkes Kaufsignal! RSI={rsi:.1f}, Umkehr erkannt")
                        return {
                            'action': 'buy',
                            'confidence': 0.75,
                            'reason': f'Strong oversold reversal (RSI: {rsi:.1f})'
                        }
            
            # VERKAUFSSIGNAL: Stark überkauft MIT Umkehr-Anzeichen
            if rsi > 70 and prev_rsi > rsi:  # RSI beginnt zu fallen
                if price >= bb_upper * 0.98:  # Nahe oberem BB
                    recent_high = recent['high'].max()
                    if price < recent_high * 0.999:  # Leichter Rückgang
                        logger.info(f"Mean Reversion: Starkes Verkaufssignal! RSI={rsi:.1f}, Umkehr erkannt")
                        return {
                            'action': 'sell',
                            'confidence': 0.75,
                            'reason': f'Strong overbought reversal (RSI: {rsi:.1f})'
                        }
            
            logger.debug(f"Mean Reversion: Keine Extremsituationen. RSI={rsi:.1f}")
            return None
            
        except Exception as e:
            logger.error(f"Fehler in Mean Reversion Strategie: {str(e)}")
            return None
    
    def _breakout_strategy(self, df: pd.DataFrame) -> Optional[Dict]:
        """Optimierte Breakout Strategie mit Volumen- und ATR-Bestätigung."""
        try:
            if len(df) < 20:
                logger.debug("Breakout: Nicht genug Daten")
                return None
            
            current = df.iloc[-1]
            recent = df.tail(20)
            logger.debug(
                "Breakout: price=%.2f high20=%.2f low20=%.2f volume=%.2f avg_vol=%.2f atr=%.5f avg_atr=%.5f",
                current['close'], recent['high'].max(), recent['low'].min(),
                current.get('volume', float('nan')), recent['volume'].mean() if 'volume' in recent.columns else float('nan'),
                current.get('atr', float('nan')), recent['atr'].mean() if 'atr' in recent.columns else float('nan')
            )
            
            if 'volume' not in df.columns or 'atr' not in df.columns:
                logger.debug("Breakout: Volume oder ATR fehlt")
                return None
            
            price = current['close']
            high_20 = recent['high'].max()
            low_20 = recent['low'].min()
            volume = current['volume']
            avg_volume = recent['volume'].mean()
            atr = current['atr']
            avg_atr = recent['atr'].mean()
            
            if pd.isna(atr) or pd.isna(avg_atr):
                return None
            
            # Kaufsignal: Echter Ausbruch mit Bestätigungen
            if price >= high_20 * 0.999:  # Nahe am 20-Tage-Hoch
                confirmations = 0
                
                # Volumen-Bestätigung (wichtig für echte Breakouts)
                if volume > avg_volume * 1.5:  # Deutlich erhöhtes Volumen
                    confirmations += 1
                
                # Volatilitäts-Bestätigung
                if atr > avg_atr * 1.1:  # Erhöhte Volatilität
                    confirmations += 1
                
                # Starker Momentum
                if price > high_20 * 1.001:  # Echter Durchbruch
                    confirmations += 1
                
                if confirmations >= 1:  # Mind. 1 Bestätigung
                    logger.info(f"Breakout: Ausbruch erkannt! Conf={confirmations}, Vol={volume/avg_volume:.1f}x")
                    return {
                        'action': 'buy',
                        'confidence': 0.70 + (confirmations * 0.05),
                        'reason': f'Confirmed breakout ({confirmations} signals, vol {volume/avg_volume:.1f}x)'
                    }
            
            # Verkaufssignal: Echter Breakdown
            if price <= low_20 * 1.001:
                confirmations = 0
                
                if volume > avg_volume * 1.5:
                    confirmations += 1
                if atr > avg_atr * 1.1:
                    confirmations += 1
                if price < low_20 * 0.999:
                    confirmations += 1
                
                if confirmations >= 1:
                    logger.info(f"Breakout: Breakdown erkannt! Conf={confirmations}, Vol={volume/avg_volume:.1f}x")
                    return {
                        'action': 'sell',
                        'confidence': 0.70 + (confirmations * 0.05),
                        'reason': f'Confirmed breakdown ({confirmations} signals, vol {volume/avg_volume:.1f}x)'
                    }
            
            logger.debug(f"Breakout: Keine bestätigten Breakouts")
            return None
            
        except Exception as e:
            logger.error(f"Fehler in Breakout Strategie: {str(e)}")
            return None
    
    def _ml_based_strategy(self, df: pd.DataFrame, predictions: Dict) -> Optional[Dict]:
        """KI-basierte Strategie unter Verwendung des ML-Modells."""
        try:
            signal = predictions.get('signal', 0)
            confidence = predictions.get('confidence', 0.0)
            
            # Mindest-Konfidenz für Handelssignal
            min_confidence = self.config.get('ml_based', {}).get('min_confidence', 0.65)
            
            if confidence >= min_confidence:
                if signal == 1:  # Kaufsignal
                    return {
                        'action': 'buy',
                        'confidence': confidence,
                        'reason': f'ML prediction (confidence: {confidence:.2%})'
                    }
                elif signal == -1:  # Verkaufssignal
                    return {
                        'action': 'sell',
                        'confidence': confidence,
                        'reason': f'ML prediction (confidence: {confidence:.2%})'
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Fehler in ML-basierter Strategie: {str(e)}")
            return None
