"""
Modul für technische Indikatoren.
Implementiert verschiedene technische Analysemethoden für den Trading-Bot.
"""

import numpy as np
import pandas as pd
import pandas_ta as ta
from typing import Dict, List, Optional, Union, Tuple
import logging

logger = logging.getLogger(__name__)

class TechnicalIndicators:
    """
    Klasse zur Berechnung technischer Indikatoren für die Marktanalyse.
    """
    
    def __init__(self, config: Dict):
        """
        Initialisiert die TechnicalIndicators-Klasse mit der angegebenen Konfiguration.
        
        Args:
            config: Dictionary mit Konfigurationen für die Indikatoren
        """
        self.config = config
        logger.info("TechnicalIndicators erfolgreich initialisiert")
    
    def calculate_all(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Berechnet alle konfigurierten Indikatoren für den übergebenen DataFrame.
        
        Args:
            df: DataFrame mit OHLCV-Daten
            
        Returns:
            DataFrame mit den berechneten Indikatoren
        """
        if df.empty:
            logger.warning("Leerer DataFrame übergeben, keine Indikatoren berechnet")
            return df
        
        # Sicherstellen, dass die notwendigen Spalten vorhanden sind
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        if not all(col in df.columns for col in required_columns):
            logger.error("Nicht alle erforderlichen Spalten im DataFrame vorhanden")
            return df
        
        # Kopie des DataFrames erstellen, um Warnungen zu vermeiden
        df = df.copy()
        
        try:
            # Gleitende Durchschnitte berechnen
            if 'sma' in self.config:
                for period in self.config['sma']:
                    df[f'sma_{period}'] = self.calculate_sma(df['close'], period)
            
            if 'ema' in self.config:
                for period in self.config['ema']:
                    df[f'ema_{period}'] = self.calculate_ema(df['close'], period)
            
            # RSI berechnen
            if 'rsi' in self.config:
                rsi_period = self.config['rsi']
                df[f'rsi_{rsi_period}'] = self.calculate_rsi(df['close'], rsi_period)
            
            # MACD berechnen
            if 'macd' in self.config:
                macd_params = self.config['macd']
                if isinstance(macd_params, dict):
                    macd = self.calculate_macd(
                        df['close'],
                        fast=macd_params.get('fast', 12),
                        slow=macd_params.get('slow', 26),
                        signal=macd_params.get('signal', 9)
                    )
                    df = pd.concat([df, macd], axis=1)
            
            # Bollinger Bänder berechnen
            if 'bollinger_bands' in self.config:
                bb_params = self.config['bollinger_bands']
                if isinstance(bb_params, dict):
                    bb = self.calculate_bollinger_bands(
                        df['close'],
                        window=bb_params.get('window', 20),
                        std_dev=bb_params.get('std_dev', 2)
                    )
                    df = pd.concat([df, bb], axis=1)
            
            # ATR berechnen
            if 'atr' in self.config:
                atr_period = self.config['atr']
                if atr_period:
                    df['atr'] = self.calculate_atr(df, atr_period)
                    logger.debug(f"ATR berechnet (Period: {atr_period})")
        
            # ADX für Trendstärke (kritisch für Trade-Qualität)
            df['adx'], df['plus_di'], df['minus_di'] = self.calculate_adx(df, 14)
            logger.debug("ADX und Directional Indicators berechnet")
        
            # Stochastic für Momentum
            df['stoch_k'], df['stoch_d'] = self.calculate_stochastic(df, 14, 3)
            logger.debug("Stochastic Oscillator berechnet")
        
            # OBV für Volumenanalyse
            df['obv'] = self.calculate_obv(df)
            logger.debug("On-Balance Volume berechnet")
        
            # VWAP für institutionelle Preisniveaus
            df['vwap'] = self.calculate_vwap(df)
            logger.debug("VWAP berechnet")
        
            # Momentum
            df['momentum'] = self.calculate_momentum(df, 10)
            logger.debug("Momentum berechnet")
            
            # Unterstützungs- und Widerstandsniveaus identifizieren
            if 'support_resistance' in self.config and self.config['support_resistance']:
                support, resistance = self.identify_support_resistance(df)
                df['support'] = support
                df['resistance'] = resistance
            
            # Volumen-Indikatoren
            if 'volume_ma' in self.config:
                for period in self.config['volume_ma']:
                    df[f'volume_ma_{period}'] = self.calculate_sma(df['volume'], period)
            
            # Chaikin Money Flow (CMF)
            try:
                cmf_period = self.config.get('cmf', {}).get('window', 20)
                df['cmf'] = ta.cmf(
                    high=df['high'], low=df['low'], close=df['close'],
                    volume=df['volume'], length=cmf_period
                )
                logger.debug(f"CMF berechnet (Period: {cmf_period})")
            except Exception as e:
                logger.warning(f"Fehler bei CMF-Berechnung: {e}")
                df['cmf'] = 0.0

            # Vortex Indicator (VI)
            try:
                vortex_period = self.config.get('vortex', {}).get('window', 14)
                vortex = ta.vortex(high=df['high'], low=df['low'], close=df['close'], length=vortex_period)
                df['vortex_pos'] = vortex[f'VIp_{vortex_period}']
                df['vortex_neg'] = vortex[f'VIm_{vortex_period}']
                logger.debug(f"Vortex Indicator berechnet (Period: {vortex_period})")
            except Exception as e:
                logger.warning(f"Fehler bei Vortex-Berechnung: {e}")
                df['vortex_pos'] = 0.5
                df['vortex_neg'] = 0.5

            # Weitere Indikatoren können hier hinzugefügt werden
            
            logger.info(f"Erfolgreich {len(df.columns) - len(required_columns)} Indikatoren berechnet")
            return df
            
        except Exception as e:
            logger.error(f"Fehler bei der Berechnung der Indikatoren: {str(e)}")
            return df
    
    @staticmethod
    def calculate_sma(series: pd.Series, period: int) -> pd.Series:
        """
        Berechnet den Simple Moving Average (SMA).
        
        Args:
            series: Zeitreihe der Schlusskurse
            period: Periode für die Berechnung
            
        Returns:
            Berechnete SMA-Werte
        """
        return ta.sma(series, length=period)
    
    @staticmethod
    def calculate_ema(series: pd.Series, period: int, **kwargs) -> pd.Series:
        """
        Berechnet den Exponential Moving Average (EMA).
        
        Args:
            series: Zeitreihe der Schlusskurse
            period: Periode für die Berechnung
            **kwargs: Zusätzliche Parameter für die EMA-Berechnung
            
        Returns:
            Berechnete EMA-Werte
        """
        return ta.ema(series, length=period, **kwargs)
    
    @staticmethod
    def calculate_rsi(series: pd.Series, period: int = 14, **kwargs) -> pd.Series:
        """
        Berechnet den Relative Strength Index (RSI).
        
        Args:
            series: Zeitreihe der Schlusskurse
            period: Periode für die Berechnung (Standard: 14)
            **kwargs: Zusätzliche Parameter für die RSI-Berechnung
            
        Returns:
            Berechnete RSI-Werte
        """
        return ta.rsi(series, length=period, **kwargs)
    
    @staticmethod
    def calculate_macd(
        series: pd.Series, 
        fast: int = 12, 
        slow: int = 26, 
        signal: int = 9, 
        **kwargs
    ) -> pd.DataFrame:
        """
        Berechnet den Moving Average Convergence Divergence (MACD).
        
        Args:
            series: Zeitreihe der Schlusskurse
            fast: Periode für den schnellen EMA
            slow: Periode für den langsamen EMA
            signal: Periode für die Signallinie
            **kwargs: Zusätzliche Parameter für die MACD-Berechnung
            
        Returns:
            DataFrame mit MACD-Linie, Signallinie und Histogramm
        """
        macd = ta.macd(
            series, 
            fast=fast, 
            slow=slow, 
            signal=signal, 
            **kwargs
        )
        
        # Spalten umbenennen für bessere Lesbarkeit
        macd.columns = ['macd_line', 'macd_signal', 'macd_hist']
        return macd
    
    @staticmethod
    def calculate_bollinger_bands(
        series: pd.Series, 
        window: int = 20, 
        std_dev: float = 2.0, 
        **kwargs
    ) -> pd.DataFrame:
        """
        Berechnet die Bollinger Bänder.
        
        Args:
            series: Zeitreihe der Schlusskurse
            window: Fenstergröße für die Berechnung
            std_dev: Anzahl der Standardabweichungen für die Bänder
            **kwargs: Zusätzliche Parameter für die Berechnung
            
        Returns:
            DataFrame mit oberem Band, mittlerer Linie (SMA) und unterem Band
        """
        bb = ta.bbands(
            series, 
            length=window, 
            std=std_dev, 
            **kwargs
        )
        
        # Spalten umbenennen für bessere Lesbarkeit
        bb.columns = ['bb_lower', 'bb_middle', 'bb_upper', 'bb_bandwidth', 'bb_percent']
        return bb[['bb_lower', 'bb_middle', 'bb_upper']]  # Nur die wichtigsten Bänder zurückgeben
    
    @staticmethod
    def calculate_atr(
        df: pd.DataFrame, 
        period: int = 14, 
        high_col: str = 'high', 
        low_col: str = 'low', 
        close_col: str = 'close',
        **kwargs
    ) -> pd.Series:
        """
        Berechnet den Average True Range (ATR).
        
        Args:
            df: DataFrame mit OHLC-Daten
            period: Periode für die Berechnung
            high_col: Name der High-Spalte
            low_col: Name der Low-Spalte
            close_col: Name der Close-Spalte
            **kwargs: Zusätzliche Parameter für die ATR-Berechnung
            
        Returns:
            Berechnete ATR-Werte
        """
        return ta.atr(
            high=df[high_col],
            low=df[low_col],
            close=df[close_col],
            length=period,
            **kwargs
        )
    
    @staticmethod
    def calculate_adx(df: pd.DataFrame, period: int = 14) -> tuple:
        """Berechnet Average Directional Index (ADX) für Trendstärke."""
        adx_data = ta.adx(
            high=df['high'],
            low=df['low'],
            close=df['close'],
            length=period
        )
        return adx_data[f'ADX_{period}'], adx_data[f'DMP_{period}'], adx_data[f'DMN_{period}']
    
    @staticmethod
    def calculate_stochastic(df: pd.DataFrame, k_period: int = 14, d_period: int = 3) -> tuple:
        """Berechnet Stochastic Oscillator für Momentum."""
        stoch = ta.stoch(
            high=df['high'],
            low=df['low'],
            close=df['close'],
            k=k_period,
            d=d_period
        )
        return stoch[f'STOCHk_{k_period}_{d_period}_3'], stoch[f'STOCHd_{k_period}_{d_period}_3']
    
    @staticmethod
    def calculate_obv(df: pd.DataFrame) -> pd.Series:
        """Berechnet On-Balance Volume (OBV) für Volumenanalyse."""
        return ta.obv(close=df['close'], volume=df['volume'])
    
    @staticmethod
    def calculate_vwap(df: pd.DataFrame) -> pd.Series:
        """Berechnet Volume Weighted Average Price (VWAP)."""
        return ta.vwap(
            high=df['high'],
            low=df['low'],
            close=df['close'],
            volume=df['volume']
        )
    
    @staticmethod
    def calculate_momentum(series: pd.Series, period: int = 10) -> pd.Series:
        """Berechnet Momentum-Indikator."""
        return ta.mom(series, length=period)
    
    @staticmethod
    def identify_support_resistance(
        df: pd.DataFrame, 
        window: int = 20, 
        tolerance: float = 0.02
    ) -> Tuple[pd.Series, pd.Series]:
        """
        Identifiziert Unterstützungs- und Widerstandsniveaus.
        
        Args:
            df: DataFrame mit OHLC-Daten
            window: Fenstergröße für die lokalen Extrema
            tolerance: Toleranzbereich für die Niveaus (in Dezimal)
            
        Returns:
            Tuple mit Unterstützungs- und Widerstandsniveaus
        """
        # Lokale Minima (Unterstützung) und Maxima (Widerstand) finden
        local_min = df['low'].rolling(window=window, center=True).min()
        local_max = df['high'].rolling(window=window, center=True).max()
        
        # Niveaus glätten und auf Toleranz prüfen
        support = local_min.copy()
        resistance = local_max.copy()
        
        # Gleitender Durchschnitt für die Glättung
        support = support.rolling(window=5, min_periods=1).mean()
        resistance = resistance.rolling(window=5, min_periods=1).mean()
        
        # Auf Toleranz prüfen
        support = support.mask(df['close'] > support * (1 + tolerance), np.nan)
        resistance = resistance.mask(df['close'] < resistance * (1 - tolerance), np.nan)
        
        # Vorwärtsfüllen der Niveaus
        support = support.ffill()
        resistance = resistance.ffill()
        
        return support, resistance
    
    @staticmethod
    def calculate_ichimoku_cloud(
        df: pd.DataFrame,
        conversion_period: int = 9,
        base_period: int = 26,
        lagging_span2_period: int = 52,
        displacement: int = 26
    ) -> pd.DataFrame:
        """
        Berechnet die Ichimoku Cloud.
        
        Args:
            df: DataFrame mit OHLC-Daten
            conversion_period: Periode für die Konvertierungslinie (Tenkan-sen)
            base_period: Periode für die Basislinie (Kijun-sen)
            lagging_span2_period: Periode für die zweite Spanne (Senkou Span B)
            displacement: Verschiebung für die Vorausschau (Chikou Span)
            
        Returns:
            DataFrame mit den Ichimoku Cloud Komponenten
        """
        high = df['high']
        low = df['low']
        close = df['close']
        
        # Tenkan-sen (Conversion Line)
        conversion_line = (high.rolling(window=conversion_period).max() + 
                         low.rolling(window=conversion_period).min()) / 2
        
        # Kijun-sen (Base Line)
        base_line = (high.rolling(window=base_period).max() + 
                    low.rolling(window=base_period).min()) / 2
        
        # Senkou Span A (Leading Span A)
        span_a = ((conversion_line + base_line) / 2).shift(displacement)
        
        # Senkou Span B (Leading Span B)
        span_b = ((high.rolling(window=lagging_span2_period).max() + 
                  low.rolling(window=lagging_span2_period).min()) / 2).shift(displacement)
        
        # Chikou Span (Lagging Span)
        lagging_span = close.shift(-displacement)
        
        # Ergebnis zusammenstellen
        ichimoku = pd.DataFrame({
            'conversion_line': conversion_line,
            'base_line': base_line,
            'span_a': span_a,
            'span_b': span_b,
            'lagging_span': lagging_span
        })
        
        return ichimoku


# Hilfsfunktion zum Testen des Moduls
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Beispielverwendung
    print("Technische Indikatoren Modul geladen.")
    print("Verwendung: Importieren Sie die TechnicalIndicators-Klasse und erstellen Sie eine Instanz.")
    
    # Beispiel für die Verwendung
    data = {
        'open': [100, 102, 101, 103, 105, 107, 106, 108],
        'high': [103, 104, 105, 107, 108, 109, 110, 112],
        'low': [99, 100, 100, 102, 103, 105, 104, 106],
        'close': [102, 101, 104, 106, 107, 106, 109, 111],
        'volume': [1000, 1200, 1100, 1500, 2000, 1800, 2200, 2500]
    }
    
    df = pd.DataFrame(data)
    
    # Indikatoren konfigurieren
    config = {
        'sma': [5, 10, 20],
        'ema': [9, 21],
        'rsi': 14,
        'macd': {'fast': 12, 'slow': 26, 'signal': 9},
        'bollinger_bands': {'window': 20, 'std_dev': 2},
        'atr': 14,
        'support_resistance': True,
        'volume_ma': [5, 20]
    }
    
    # Indikatoren berechnen
    ti = TechnicalIndicators(config=config)
    df_with_indicators = ti.calculate_all(df)
    
    print("\nDaten mit Indikatoren:")
    print(df_with_indicators)
