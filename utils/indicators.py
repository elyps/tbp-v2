import pandas as pd
import numpy as np
import pandas_ta as ta
from typing import List, Dict, Union, Optional
import warnings
warnings.filterwarnings('ignore')

class TechnicalIndicators:
    """
    A comprehensive class for calculating various technical indicators.
    Wraps around pandas_ta for most calculations but adds custom implementations where needed.
    """
    
    @staticmethod
    def add_all_indicators(
        df: pd.DataFrame,
        indicators_config: Dict[str, dict],
        close_col: str = 'close',
        high_col: str = 'high',
        low_col: str = 'low',
        volume_col: str = 'volume'
    ) -> pd.DataFrame:
        """
        Add multiple technical indicators to the DataFrame based on configuration
        
        Args:
            df: DataFrame with price data
            indicators_config: Dictionary with indicator configurations
                              Example: {'sma': {'length': 20}, 'rsi': {'length': 14}}
            close_col: Name of the close price column
            high_col: Name of the high price column
            low_col: Name of the low price column
            volume_col: Name of the volume column
            
        Returns:
            DataFrame with added indicator columns
        """
        df = df.copy()
        
        # Ensure required columns exist
        required_cols = [close_col, high_col, low_col, volume_col]
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"Required column '{col}' not found in DataFrame")
        
        # Process each indicator
        for indicator, params in indicators_config.items():
            if not params.get('enabled', True):
                continue
                
            if indicator == 'sma':
                df = TechnicalIndicators.add_sma(
                    df, 
                    length=params.get('length', 20),
                    col=close_col
                )
            elif indicator == 'ema':
                df = TechnicalIndicators.add_ema(
                    df,
                    length=params.get('length', 20),
                    col=close_col
                )
            elif indicator == 'rsi':
                df = TechnicalIndicators.add_rsi(
                    df,
                    length=params.get('length', 14),
                    col=close_col
                )
            elif indicator == 'macd':
                df = TechnicalIndicators.add_macd(
                    df,
                    fast=params.get('fast', 12),
                    slow=params.get('slow', 26),
                    signal=params.get('signal', 9),
                    col=close_col
                )
            elif indicator == 'bollinger_bands':
                df = TechnicalIndicators.add_bollinger_bands(
                    df,
                    length=params.get('length', 20),
                    std=params.get('std', 2),
                    col=close_col
                )
            elif indicator == 'stochastic':
                df = TechnicalIndicators.add_stochastic(
                    df,
                    k=params.get('k', 14),
                    d=params.get('d', 3),
                    smooth_k=params.get('smooth_k', 3),
                    high_col=high_col,
                    low_col=low_col,
                    close_col=close_col
                )
            elif indicator == 'atr':
                df = TechnicalIndicators.add_atr(
                    df,
                    length=params.get('length', 14),
                    high_col=high_col,
                    low_col=low_col,
                    close_col=close_col
                )
            elif indicator == 'obv':
                df = TechnicalIndicators.add_obv(
                    df,
                    close_col=close_col,
                    volume_col=volume_col
                )
            elif indicator == 'ichimoku':
                df = TechnicalIndicators.add_ichimoku(
                    df,
                    tenkan=params.get('tenkan', 9),
                    kijun=params.get('kijun', 26),
                    senkou=params.get('senkou', 52),
                    chikou=params.get('chikou', 26),
                    high_col=high_col,
                    low_col=low_col,
                    close_col=close_col
                )
            elif indicator == 'vwap':
                df = TechnicalIndicators.add_vwap(
                    df,
                    high_col=high_col,
                    low_col=low_col,
                    close_col=close_col,
                    volume_col=volume_col
                )
            elif indicator == 'adx':
                df = TechnicalIndicators.add_adx(
                    df,
                    length=params.get('length', 14),
                    high_col=high_col,
                    low_col=low_col,
                    close_col=close_col
                )
            # Add more indicators as needed
            
        return df
    
    # ======================
    # Individual Indicators
    # ======================
    
    @staticmethod
    def add_sma(df: pd.DataFrame, length: int = 20, col: str = 'close') -> pd.DataFrame:
        """Add Simple Moving Average"""
        df[f'sma_{length}'] = ta.sma(df[col], length=length)
        return df
    
    @staticmethod
    def add_ema(df: pd.DataFrame, length: int = 20, col: str = 'close') -> pd.DataFrame:
        """Add Exponential Moving Average"""
        df[f'ema_{length}'] = ta.ema(df[col], length=length)
        return df
    
    @staticmethod
    def add_rsi(df: pd.DataFrame, length: int = 14, col: str = 'close') -> pd.DataFrame:
        """Add Relative Strength Index"""
        df[f'rsi_{length}'] = ta.rsi(df[col], length=length)
        return df
    
    @staticmethod
    def add_macd(
        df: pd.DataFrame, 
        fast: int = 12, 
        slow: int = 26, 
        signal: int = 9,
        col: str = 'close'
    ) -> pd.DataFrame:
        """Add Moving Average Convergence Divergence"""
        macd = ta.macd(df[col], fast=fast, slow=slow, signal=signal)
        df = pd.concat([df, macd], axis=1)
        return df
    
    @staticmethod
    def add_bollinger_bands(
        df: pd.DataFrame, 
        length: int = 20, 
        std: float = 2.0,
        col: str = 'close'
    ) -> pd.DataFrame:
        """Add Bollinger Bands"""
        bbands = ta.bbands(df[col], length=length, std=std)
        df = pd.concat([df, bbands], axis=1)
        return df
    
    @staticmethod
    def add_stochastic(
        df: pd.DataFrame, 
        k: int = 14, 
        d: int = 3, 
        smooth_k: int = 3,
        high_col: str = 'high',
        low_col: str = 'low',
        close_col: str = 'close'
    ) -> pd.DataFrame:
        """Add Stochastic Oscillator"""
        stoch = ta.stoch(
            high=df[high_col],
            low=df[low_col],
            close=df[close_col],
            k=k,
            d=d,
            smooth_k=smooth_k
        )
        df = pd.concat([df, stoch], axis=1)
        return df
    
    @staticmethod
    def add_atr(
        df: pd.DataFrame, 
        length: int = 14,
        high_col: str = 'high',
        low_col: str = 'low',
        close_col: str = 'close'
    ) -> pd.DataFrame:
        """Add Average True Range"""
        atr = ta.atr(
            high=df[high_col],
            low=df[low_col],
            close=df[close_col],
            length=length
        )
        df['atr'] = atr
        return df
    
    @staticmethod
    def add_obv(
        df: pd.DataFrame, 
        close_col: str = 'close',
        volume_col: str = 'volume'
    ) -> pd.DataFrame:
        """Add On-Balance Volume"""
        df['obv'] = ta.obv(df[close_col], df[volume_col])
        return df
    
    @staticmethod
    def add_ichimoku(
        df: pd.DataFrame,
        tenkan: int = 9,
        kijun: int = 26,
        senkou: int = 52,
        chikou: int = 26,
        high_col: str = 'high',
        low_col: str = 'low',
        close_col: str = 'close'
    ) -> pd.DataFrame:
        """Add Ichimoku Cloud"""
        ichimoku = ta.ichimoku(
            high=df[high_col],
            low=df[low_col],
            tenkan=tenkan,
            kijun=kijun,
            senkou=senkou
        )
        
        # Rename columns for clarity
        ichimoku = ichimoku[0].rename(columns={
            'ITS_9': 'tenkan_sen',
            'IKS_26': 'kijun_sen',
            'ISA_9': 'senkou_span_a',
            'ISB_26': 'senkou_span_b',
            'ITS_9_26_52': 'chikou_span'
        })
        
        # Add to the original DataFrame
        df = pd.concat([df, ichimoku], axis=1)
        
        # Add chikou span (shifted back)
        if 'chikou_span' in df.columns:
            df['chikou_span'] = df[close_col].shift(-chikou)
            
        return df
    
    @staticmethod
    def add_vwap(
        df: pd.DataFrame,
        high_col: str = 'high',
        low_col: str = 'low',
        close_col: str = 'close',
        volume_col: str = 'volume'
    ) -> pd.DataFrame:
        """Add Volume Weighted Average Price"""
        # VWAP is typically calculated on a per-session basis
        # This is a simplified version
        df['vwap'] = (df[close_col] * df[volume_col]).cumsum() / df[volume_col].cumsum()
        return df
    
    @staticmethod
    def add_adx(
        df: pd.DataFrame,
        length: int = 14,
        high_col: str = 'high',
        low_col: str = 'low',
        close_col: str = 'close'
    ) -> pd.DataFrame:
        """Add Average Directional Index"""
        adx = ta.adx(
            high=df[high_col],
            low=df[low_col],
            close=df[close_col],
            length=length
        )
        df = pd.concat([df, adx], axis=1)
        return df
    
    # ======================
    # Custom Indicators
    # ======================
    
    @staticmethod
    def add_supertrend(
        df: pd.DataFrame,
        period: int = 10,
        multiplier: float = 3.0,
        high_col: str = 'high',
        low_col: str = 'low',
        close_col: str = 'close'
    ) -> pd.DataFrame:
        """
        Add Supertrend indicator
        
        Args:
            df: DataFrame with price data
            period: Lookback period for ATR
            multiplier: ATR multiplier
            high_col: High price column name
            low_col: Low price column name
            close_col: Close price column name
            
        Returns:
            DataFrame with Supertrend columns added
        """
        # Calculate ATR
        df = TechnicalIndicators.add_atr(df, period, high_col, low_col, close_col)
        
        # Calculate basic upper and lower bands
        df['hl2'] = (df[high_col] + df[low_col]) / 2
        df['upper_band'] = df['hl2'] + (multiplier * df['atr'])
        df['lower_band'] = df['hl2'] - (multiplier * df['atr'])
        
        # Initialize columns
        df['in_uptrend'] = True
        df['super_trend'] = 0.0
        
        # Calculate Supertrend
        for i in range(1, len(df)):
            current = df.index[i]
            previous = df.index[i-1]
            
            # Current close
            close = df.loc[current, close_col]
            
            # Current upper and lower bands
            upper_band = df.loc[current, 'upper_band']
            lower_band = df.loc[current, 'lower_band']
            
            # Previous Supertrend and trend
            prev_upper_band = df.loc[previous, 'upper_band']
            prev_lower_band = df.loc[previous, 'lower_band']
            prev_super_trend = df.loc[previous, 'super_trend']
            prev_trend = df.loc[previous, 'in_uptrend']
            
            # Adjust bands
            if (df.loc[current, 'upper_band'] < prev_upper_band) or (df.loc[previous, close_col] > prev_upper_band):
                df.loc[current, 'upper_band'] = df.loc[current, 'upper_band']
            else:
                df.loc[current, 'upper_band'] = prev_upper_band
                
            if (df.loc[current, 'lower_band'] > prev_lower_band) or (df.loc[previous, close_col] < prev_lower_band):
                df.loc[current, 'lower_band'] = df.loc[current, 'lower_band']
            else:
                df.loc[current, 'lower_band'] = prev_lower_band
            
            # Determine trend and Supertrend
            if close > df.loc[current, 'upper_band']:
                df.loc[current, 'in_uptrend'] = True
            elif close < df.loc[current, 'lower_band']:
                df.loc[current, 'in_uptrend'] = False
            else:
                df.loc[current, 'in_uptrend'] = prev_trend
                
                if df.loc[current, 'in_uptrend'] and (df.loc[current, 'lower_band'] < df.loc[previous, 'lower_band']):
                    df.loc[current, 'lower_band'] = df.loc[previous, 'lower_band']
                    
                if not df.loc[current, 'in_uptrend'] and (df.loc[current, 'upper_band'] > df.loc[previous, 'upper_band']):
                    df.loc[current, 'upper_band'] = df.loc[previous, 'upper_band']
            
            # Set Supertrend value
            if df.loc[current, 'in_uptrend']:
                df.loc[current, 'super_trend'] = df.loc[current, 'lower_band']
            else:
                df.loc[current, 'super_trend'] = df.loc[current, 'upper_band']
        
        # Clean up intermediate columns
        df.drop(['hl2', 'upper_band', 'lower_band'], axis=1, inplace=True, errors='ignore')
        
        return df
    
    @staticmethod
    def add_volume_profile(
        df: pd.DataFrame, 
        price_bins: int = 20,
        volume_col: str = 'volume',
        price_col: str = 'close'
    ) -> pd.DataFrame:
        """
        Add Volume Profile indicator
        
        Args:
            df: DataFrame with price and volume data
            price_bins: Number of price levels to divide the range into
            volume_col: Volume column name
            price_col: Price column name
            
        Returns:
            DataFrame with Volume Profile columns added
        """
        # Calculate price range
        price_min = df[price_col].min()
        price_max = df[price_col].max()
        bin_size = (price_max - price_min) / price_bins
        
        # Create price bins
        bins = [price_min + i * bin_size for i in range(price_bins + 1)]
        labels = [f"{bins[i]:.2f}-{bins[i+1]:.2f}" for i in range(price_bins)]
        
        # Assign each price to a bin
        df['price_bin'] = pd.cut(
            df[price_col], 
            bins=bins, 
            labels=labels,
            include_lowest=True
        )
        
        # Calculate volume per price bin
        volume_profile = df.groupby('price_bin')[volume_col].sum().sort_index(ascending=False)
        
        # Add to original DataFrame
        df = df.join(volume_profile.rename('volume_profile'), on='price_bin')
        
        # Clean up
        df.drop('price_bin', axis=1, inplace=True)
        
        return df
